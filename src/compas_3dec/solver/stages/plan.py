import re
from math import sqrt

from compas.data import Data


def _value(item, name, default=None):
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def _stage_name(group, kind, used):
    """Return a filesystem-safe, unique stage name derived from a DEM group."""
    label = str(getattr(group, "name", "") or kind).strip().lower()
    label = re.sub(r"[^a-z0-9]+", "-", label).strip("-") or kind
    base = "{}-{}".format(label, kind)
    name = base
    index = 2
    while name in used:
        name = "{}-{}".format(base, index)
        index += 1
    used.add(name)
    return name


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


def _validate_gravity_order(stages):
    """Require gravity to be the first physical stage when loads are present."""
    physical = [stage for stage in stages if stage.kind != "initialization"]
    gravity_indices = [index for index, stage in enumerate(physical) if stage.kind == "gravity"]
    boundary_indices = [index for index, stage in enumerate(physical) if stage.kind in ("loads", "displacements")]
    if len(gravity_indices) > 1:
        raise ValueError("An analysis can contain only one gravity stage.")
    if boundary_indices and gravity_indices != [0]:
        raise ValueError("Analyses with loads or displacements require exactly one gravity stage, and gravity must be first.")


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
        """Build initialisation, gravity, load and displacement stages.

        COMPAS DEM boundary-condition groups become sequential 3DEC stages in
        their registered order. Gravity is extracted into the mandatory first
        stage. A group containing both loads and prescribed displacements is
        split into a load stage followed by a displacement stage. Supports are
        read from the model during analysis preparation; prescribed zero
        translations are not reinterpreted as supports.
        """
        supports = set(analysis.supports)
        direct_stages = list(getattr(analysis, "stages", []) or [])
        if direct_stages:
            if any(stage.kind == "initialization" for stage in direct_stages):
                stages = direct_stages
            else:
                stages = [ThreeDECStage(name="initialization", kind="initialization")] + direct_stages
            _validate_gravity_order(stages)
            return cls(
                name="{} stages".format(analysis.name),
                stages=stages,
                supports=supports,
            )

        gravity_values = set()
        gravity_sources = []
        for boundary_condition in analysis.boundary_conditions:
            gravity = getattr(boundary_condition, "g", None)
            if gravity is not None:
                gravity_values.add(float(gravity))
                gravity_sources.append(str(boundary_condition.guid))

        if len(gravity_values) > 1:
            raise ValueError("Boundary conditions specify different gravity values: {}.".format(sorted(gravity_values)))

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

        boundary_conditions = list(analysis.boundary_conditions)
        configured_stages = solver_parameters.get("stages")
        phase_by_guid = {}
        if configured_stages:
            by_name = {str(_value(condition, "name", "")): condition for condition in boundary_conditions}
            configured_names = [str(name) for phase in configured_stages for name in phase]
            unknown = [name for name in configured_names if name not in by_name]
            missing = [name for name in by_name if name not in configured_names]
            if unknown or missing or len(configured_names) != len(set(configured_names)):
                raise ValueError(
                    "Invalid 3DEC stage plan. Unknown: {}; missing: {}; duplicate names: {}.".format(
                        unknown,
                        missing,
                        len(configured_names) != len(set(configured_names)),
                    )
                )
            boundary_conditions = [by_name[name] for name in configured_names]
            for phase_index, phase in enumerate(configured_stages):
                conditions = [by_name[str(name)] for name in phase]
                if len(conditions) > 1 and any(_value(condition, "displacements", []) for condition in conditions):
                    raise ValueError("A 3DEC stage containing prescribed displacements cannot contain another boundary-condition group.")
                for condition in conditions:
                    phase_by_guid[str(_value(condition, "guid"))] = phase_index

        blocks = {int(block["node"]): block for block in analysis.blocks}
        stages = [ThreeDECStage(name="initialization", kind="initialization")]
        if gravity_values:
            stages.append(
                ThreeDECStage(
                    name="gravity",
                    kind="gravity",
                    gravity=next(iter(gravity_values)),
                    source_boundary_conditions=gravity_sources,
                    options=solve_options,
                )
            )

        used_names = {stage.name for stage in stages}
        load_stages = {}
        for boundary_index, boundary_condition in enumerate(boundary_conditions):
            source = [str(boundary_condition.guid)]
            body_forces = list(boundary_condition.body_forces)
            point_loads = [
                _direct_point_load(
                    load,
                    default_steps=solver_parameters.get("load_steps", 1),
                    default_radius=solver_parameters.get("load_radius", 0.01),
                )
                for load in boundary_condition.point_loads
            ]
            surface_loads = [
                _direct_surface_load(
                    load,
                    blocks,
                    default_steps=solver_parameters.get("load_steps", 1),
                    range_tolerance=solver_parameters.get("surface_load_range_tolerance"),
                )
                for load in boundary_condition.surface_loads
            ]
            displacements = [
                item
                for item in (
                    _direct_displacement(
                        displacement,
                        default_steps=solver_parameters.get("displacement_steps", 1),
                    )
                    for displacement in boundary_condition.displacements
                )
                if item is not None
            ]

            if body_forces or point_loads or surface_loads:
                phase_key = phase_by_guid.get(str(boundary_condition.guid), boundary_index)
                load_stage = load_stages.get(phase_key)
                if load_stage is None:
                    load_stage = ThreeDECStage(
                        name=_stage_name(boundary_condition, "loads", used_names),
                        kind="loads",
                        body_forces=body_forces,
                        point_loads=point_loads,
                        surface_loads=surface_loads,
                        source_boundary_conditions=source,
                        options=solve_options,
                    )
                    stages.append(load_stage)
                    load_stages[phase_key] = load_stage
                else:
                    load_stage.body_forces.extend(body_forces)
                    load_stage.point_loads.extend(point_loads)
                    load_stage.surface_loads.extend(surface_loads)
                    load_stage.source_boundary_conditions.extend(source)
            if displacements:
                stages.append(
                    ThreeDECStage(
                        name=_stage_name(boundary_condition, "displacements", used_names),
                        kind="displacements",
                        displacements=displacements,
                        source_boundary_conditions=source,
                        options=displacement_options,
                    )
                )

        _validate_gravity_order(stages)
        return cls(
            name="{} stages".format(analysis.name),
            stages=stages,
            supports=supports,
        )

    def stage(self, kind):
        """Return the first stage of a given kind.

        Parameters
        ----------
        kind : str
            Semantic stage kind.

        Returns
        -------
        :class:`ThreeDECStage` | None
            The first matching stage, or ``None`` when no match exists.
        """
        for stage in self.stages:
            if stage.kind == kind:
                return stage
        return None
