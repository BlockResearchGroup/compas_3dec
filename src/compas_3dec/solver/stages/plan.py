from math import sqrt

from compas.data import Data


def _value(item, name, default=None):
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def _direct_point_load(load, default_steps=1, default_radius=0.01):
    """Convert a COMPAS DEM point load to the direct load schema."""
    force = [float(value) for value in _value(load, "force", [0.0, 0.0, 0.0])]
    magnitude = sqrt(sum(value * value for value in force))
    if magnitude <= 1e-30:
        raise NotImplementedError("Pure point moments are not yet supported by 3DEC.")
    direction = [value / magnitude for value in force]
    block = int(_value(load, "block_index"))
    steps = int(_value(load, "steps", _value(load, "load_steps", default_steps)))
    point = _value(load, "point")
    common = {
        "name": _value(load, "name", "COMPAS DEM point load"),
        "magnitude": magnitude,
        "direction": direction,
        "steps": steps,
    }
    if point is None:
        common.update(kind="centroid", blocks=[block])
    else:
        common.update(
            kind="sphere",
            point=[float(value) for value in point],
            radius=float(_value(load, "radius", default_radius)),
            block=block,
            distribution_count=int(_value(load, "distribution_count", 1)),
        )
    return common


def _direct_surface_load(load, blocks, default_steps=1, range_tolerance=None):
    """Convert a COMPAS DEM face traction to the native 3DEC stress schema."""
    node = int(_value(load, "block_index"))
    face = int(_value(load, "face_index"))
    block = blocks.get(node)
    if block is None:
        raise ValueError("Surface load references unknown block {}.".format(node))
    mesh = block["geometry"]
    if face not in list(mesh.faces()):
        raise ValueError("Surface load references unknown face {} of block {}.".format(face, node))
    traction = [float(value) for value in _value(load, "load")]
    normal = [float(value) for value in mesh.face_normal(face)]
    dot = sum(traction[i] * normal[i] for i in range(3))
    tensor = [[traction[i] * normal[j] + normal[i] * traction[j] - dot * normal[i] * normal[j] for j in range(3)] for i in range(3)]
    coordinates = list(mesh.vertices_attributes("xyz"))
    size = max(max(row[i] for row in coordinates) - min(row[i] for row in coordinates) for i in range(3))
    tolerance = float(range_tolerance) if range_tolerance is not None else max(size * 1e-6, 1e-9)
    return {
        "kind": "surface_stress",
        "name": _value(load, "name", "COMPAS DEM surface load"),
        "block": node,
        "face": face,
        "stress": [tensor[0][0], tensor[1][1], tensor[2][2], tensor[0][1], tensor[1][2], tensor[2][0]],
        "traction": traction,
        "steps": int(_value(load, "steps", _value(load, "load_steps", default_steps))),
        "face_vertices": [list(mesh.vertex_coordinates(vertex)) for vertex in mesh.face_vertices(face)],
        "face_center": list(mesh.face_center(face)),
        "face_normal": normal,
        "face_area": float(mesh.face_area(face)),
        "range_tolerance": tolerance,
    }


def _direct_displacement(displacement, default_steps=1):
    """Convert a COMPAS DEM translation to the native stepped schema."""
    rotation = _value(displacement, "rotation")
    if rotation is not None:
        raise NotImplementedError("COMPAS DEM prescribed rotations are not yet supported by 3DEC.")
    translation = _value(displacement, "translation")
    if translation is None:
        raise TypeError("Unsupported COMPAS DEM displacement type: {}.".format(type(displacement).__name__))
    active = [value is not None for value in translation]
    vector = [0.0 if value is None else float(value) for value in translation]
    magnitude = sqrt(sum(value * value for value in vector))
    if magnitude <= 1e-30:
        return None
    return {
        "kind": "translation",
        "name": _value(displacement, "name", "COMPAS DEM prescribed translation"),
        "blocks": [int(_value(displacement, "block_index"))],
        "magnitude": magnitude,
        "direction": [value / magnitude for value in vector],
        "steps": int(_value(displacement, "steps", _value(displacement, "displacement_steps", default_steps))),
        "active_components": active,
    }


class ThreeDECStage(Data):
    """Portable description of one semantic analysis stage."""

    CURRENT_SCHEMA_VERSION = 1

    def __init__(
        self,
        name,
        kind,
        gravity=None,
        body_forces=None,
        point_loads=None,
        surface_loads=None,
        displacements=None,
        source_boundary_conditions=None,
        options=None,
        schema_version=None,
    ):
        super().__init__(name=name)
        self.schema_version = schema_version or self.CURRENT_SCHEMA_VERSION
        self.kind = str(kind)
        self.gravity = gravity
        self.body_forces = list(body_forces or [])
        self.point_loads = list(point_loads or [])
        self.surface_loads = list(surface_loads or [])
        self.displacements = list(displacements or [])
        self.source_boundary_conditions = list(source_boundary_conditions or [])
        self.options = dict(options or {})

    @property
    def __data__(self):
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "kind": self.kind,
            "gravity": self.gravity,
            "body_forces": self.body_forces,
            "point_loads": self.point_loads,
            "surface_loads": self.surface_loads,
            "displacements": self.displacements,
            "source_boundary_conditions": self.source_boundary_conditions,
            "options": self.options,
        }


class ThreeDECStagePlan(Data):
    """Ordered semantic stages derived from a prepared analysis."""

    CURRENT_SCHEMA_VERSION = 1

    def __init__(self, stages=None, supports=None, schema_version=None, name=None):
        super().__init__(name=name)
        self.schema_version = schema_version or self.CURRENT_SCHEMA_VERSION
        self.stages = list(stages or [])
        self.supports = sorted(set(int(node) for node in (supports or [])))

    @property
    def __data__(self):
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "stages": self.stages,
            "supports": self.supports,
        }

    @classmethod
    def from_analysis(cls, analysis):
        """Build initialization, gravity, load and displacement stages.

        Multiple COMPAS DEM boundary-condition groups are combined because the
        current ``Problem.solve`` contract solves them concurrently. Supports
        are read from the model during analysis preparation; prescribed zero
        translations are not reinterpreted as supports.
        """
        supports = set(analysis.supports)
        direct_stages = list(getattr(analysis, "stages", []) or [])
        if direct_stages:
            if any(stage.kind == "initialization" for stage in direct_stages):
                stages = direct_stages
            else:
                stages = [ThreeDECStage(name="initialization", kind="initialization")] + direct_stages
            return cls(
                name="{} stages".format(analysis.name),
                stages=stages,
                supports=supports,
            )

        gravity_values = set()
        body_forces = []
        point_loads = []
        surface_loads = []
        displacements = []
        sources = []

        for boundary_condition in analysis.boundary_conditions:
            sources.append(str(boundary_condition.guid))
            gravity = getattr(boundary_condition, "g", None)
            if gravity is not None:
                gravity_values.add(float(gravity))
            body_forces.extend(list(boundary_condition.body_forces))
            point_loads.extend(list(boundary_condition.point_loads))
            surface_loads.extend(list(boundary_condition.surface_loads))

            displacements.extend(list(boundary_condition.displacements))

        if len(gravity_values) > 1:
            raise ValueError("Concurrent boundary conditions specify different gravity values: {}.".format(sorted(gravity_values)))

        solver_parameters = {}
        if analysis.solver_configuration is not None:
            if isinstance(analysis.solver_configuration, dict):
                solver_parameters.update(analysis.solver_configuration.get("parameters", {}) or {})
            else:
                solver_parameters.update(getattr(analysis.solver_configuration, "parameters", {}) or {})

        solve_options = {
            "ratio": solver_parameters.get("ratio", 1e-5),
            "ratio_keyword": solver_parameters.get("ratio_keyword", "ratio-local"),
            "time": solver_parameters.get("time", 1.0),
            "gravity_steps": solver_parameters.get("gravity_steps", 10),
            "solve_time": solver_parameters.get("load_solve_time"),
            "cycles": solver_parameters.get("load_cycles", 15000),
            "save_steps": solver_parameters.get("save_load_steps", True),
            "stop_on_nonconvergence": solver_parameters.get("stop_on_nonconvergence", True),
            "damping": solver_parameters.get("load_damping", "global"),
        }
        displacement_options = {
            "motion_time": solver_parameters.get("displacement_motion_time", 1.0),
            "source_state": solver_parameters.get("displacement_source_state", "auto"),
            "ratio": solver_parameters.get("displacement_ratio", solver_parameters.get("ratio", 1e-5)),
            "ratio_keyword": solver_parameters.get("displacement_ratio_keyword", solver_parameters.get("ratio_keyword", "ratio-local")),
            "equilibrium_time": solver_parameters.get("displacement_equilibrium_time"),
            "equilibrium_cycles": solver_parameters.get("displacement_equilibrium_cycles", 15000),
            "save_steps": solver_parameters.get("save_displacement_steps", True),
            "stop_on_nonconvergence": solver_parameters.get("stop_on_nonconvergence", True),
            "damping": solver_parameters.get("displacement_damping", "local"),
        }

        point_loads = [
            _direct_point_load(
                load,
                default_steps=solver_parameters.get("load_steps", 1),
                default_radius=solver_parameters.get("load_radius", 0.01),
            )
            for load in point_loads
        ]
        blocks = {int(block["node"]): block for block in analysis.blocks}
        surface_loads = [
            _direct_surface_load(
                load,
                blocks,
                default_steps=solver_parameters.get("load_steps", 1),
                range_tolerance=solver_parameters.get("surface_load_range_tolerance"),
            )
            for load in surface_loads
        ]
        displacements = [
            item
            for item in (
                _direct_displacement(
                    displacement,
                    default_steps=solver_parameters.get("displacement_steps", 1),
                )
                for displacement in displacements
            )
            if item is not None
        ]

        stages = [ThreeDECStage(name="initialization", kind="initialization")]
        if gravity_values:
            stages.append(
                ThreeDECStage(
                    name="gravity",
                    kind="gravity",
                    gravity=next(iter(gravity_values)),
                    source_boundary_conditions=sources,
                    options=solve_options,
                )
            )
        if body_forces or point_loads or surface_loads:
            stages.append(
                ThreeDECStage(
                    name="loads",
                    kind="loads",
                    body_forces=body_forces,
                    point_loads=point_loads,
                    surface_loads=surface_loads,
                    source_boundary_conditions=sources,
                    options=solve_options,
                )
            )
        if displacements:
            stages.append(
                ThreeDECStage(
                    name="displacements",
                    kind="displacements",
                    displacements=displacements,
                    source_boundary_conditions=sources,
                    options=displacement_options,
                )
            )

        return cls(
            name="{} stages".format(analysis.name),
            stages=stages,
            supports=supports,
        )

    def stage(self, kind):
        for stage in self.stages:
            if stage.kind == kind:
                return stage
        return None
