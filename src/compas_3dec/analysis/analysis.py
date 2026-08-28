from compas.data import Data

from .mapping import ThreeDECEntityMap

_RUNTIME_SOLVER_PARAMETERS = {
    "arguments",
    "executable",
    "suppress_output",
    "timeout",
    "workspace",
}


def _portable_solver_configuration(solver):
    """Return only solver settings that belong to a portable analysis."""
    if solver is None:
        return None

    if isinstance(solver, dict):
        name = solver.get("name")
        parameters = solver.get("parameters", {})
    else:
        name = getattr(solver, "name", None)
        parameters = getattr(solver, "parameters", {})

    parameters = {key: value for key, value in (parameters or {}).items() if key not in _RUNTIME_SOLVER_PARAMETERS}
    return {"name": name, "parameters": parameters}


class ThreeDECAnalysis(Data):
    """Portable prepared input for a 3DEC analysis.

    The analysis is a serialisable snapshot. Runtime configuration such as an
    executable path or working directory belongs to :class:`ThreeDECSolver`
    and is intentionally excluded.
    """

    CURRENT_SCHEMA_VERSION = 3

    def __init__(
        self,
        model_id,
        problem_id,
        blocks=None,
        interfaces=None,
        supports=None,
        boundary_conditions=None,
        stages=None,
        contact_properties=None,
        contact_property_overrides=None,
        contact_block_pair_overrides=None,
        solver_configuration=None,
        entity_map=None,
        source="direct",
        schema_version=None,
        name=None,
    ):
        super().__init__(name=name)
        self.schema_version = schema_version or self.CURRENT_SCHEMA_VERSION
        self.model_id = str(model_id)
        self.problem_id = str(problem_id)
        self.blocks = list(blocks or [])
        self.interfaces = list(interfaces or [])
        self.supports = sorted(set(int(node) for node in (supports or [])))
        self.boundary_conditions = list(boundary_conditions or [])
        self.stages = list(stages or [])
        self.contact_properties = contact_properties
        self.contact_property_overrides = list(contact_property_overrides or [])
        self.contact_block_pair_overrides = list(contact_block_pair_overrides or [])
        self.solver_configuration = solver_configuration
        self.entity_map = entity_map or ThreeDECEntityMap()
        self.source = str(source)

    @property
    def __data__(self):
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "model_id": self.model_id,
            "problem_id": self.problem_id,
            "blocks": self.blocks,
            "interfaces": self.interfaces,
            "supports": self.supports,
            "boundary_conditions": self.boundary_conditions,
            "stages": self.stages,
            "contact_properties": self.contact_properties,
            "contact_property_overrides": self.contact_property_overrides,
            "contact_block_pair_overrides": self.contact_block_pair_overrides,
            "solver_configuration": self.solver_configuration,
            "entity_map": self.entity_map,
            "source": self.source,
        }

    @classmethod
    def __from_data__(cls, data):
        supports = data.get("supports")
        if supports is None:
            supports = [block["node"] for block in data.get("blocks", []) if block.get("is_support")]
        return cls(
            name=data.get("name"),
            schema_version=data.get("schema_version", 1),
            model_id=data["model_id"],
            problem_id=data["problem_id"],
            blocks=data.get("blocks", []),
            interfaces=data.get("interfaces", []),
            supports=supports,
            boundary_conditions=data.get("boundary_conditions", []),
            stages=data.get("stages", []),
            contact_properties=data.get("contact_properties"),
            contact_property_overrides=data.get("contact_property_overrides", []),
            contact_block_pair_overrides=data.get("contact_block_pair_overrides", []),
            solver_configuration=_portable_solver_configuration(data.get("solver_configuration")),
            entity_map=data.get("entity_map"),
            source=("direct" if data.get("source") == "standalone" else data.get("source", "unknown")),
        )

    @classmethod
    def from_blockmodel(cls, model, problem):
        """Create a prepared analysis from a COMPAS DEM model and problem.

        The method uses public model/problem data wherever available, without
        retaining either complete object. The COMPAS graph node is deliberately
        reused as the 3DEC region number.

        Parameters
        ----------
        model : compas_dem.models.BlockModel
            Source block model.
        problem : compas_dem.problem.Problem
            Loads, supports, contact properties and solver options.
        """
        model_id = str(model.guid)
        problem_model_id = str(problem.model_id)
        if problem_model_id != model_id:
            raise ValueError(
                "Problem model_id {} does not match model GUID {}.".format(
                    problem_model_id,
                    model_id,
                )
            )

        entity_map = ThreeDECEntityMap(name="{} entity map".format(problem.name or "3DEC"))
        blocks = []
        # Supports belong to the BlockModel in the refactored compas_dem API.
        # Keep the attribute fallback temporarily so analysis snapshots can
        # still be prepared from the earlier integration branch.
        supports = set(int(node) for node in getattr(problem, "supports", []))

        for element in model.elements():
            node = element.graphnode
            if not isinstance(node, int):
                raise TypeError("COMPAS DEM graph node identifiers must be integers; got {!r}.".format(node))

            geometry = element.modelgeometry.copy()
            vertices = [(vertex, geometry.vertex_coordinates(vertex)) for vertex in geometry.vertices()]
            entity_map.add_block(
                node=node,
                element_guid=element.guid,
                region=node,
                vertices=vertices,
            )
            blocks.append(
                {
                    "node": node,
                    "element_guid": str(element.guid),
                    "region": node,
                    "name": element.name,
                    "geometry": geometry,
                    "material": element.material,
                    "group": ("supports" if bool(getattr(element, "is_support", False)) else "block"),
                    "is_support": bool(getattr(element, "is_support", False)),
                }
            )
            if getattr(element, "is_support", False):
                supports.add(node)

        interfaces = []
        for edge in model.graph.edges():
            u, v = int(edge[0]), int(edge[1])
            entity_map.add_edge((u, v))
            contacts = model.graph.edge_attribute((u, v), name="contacts") or []
            interfaces.append(
                {
                    "edge": [u, v],
                    "regions": [
                        entity_map.region_for_node(u),
                        entity_map.region_for_node(v),
                    ],
                    "contacts": list(contacts),
                }
            )

        problem_data = problem.__data__
        return cls(
            name=problem.name,
            model_id=model_id,
            problem_id=str(problem.guid),
            blocks=blocks,
            interfaces=interfaces,
            supports=supports,
            boundary_conditions=list(problem.boundary_conditions),
            contact_properties=problem.contact_properties,
            contact_property_overrides=[],
            contact_block_pair_overrides=[],
            solver_configuration=_portable_solver_configuration(problem_data.get("solver")),
            entity_map=entity_map,
            source="compas_dem",
        )

    @classmethod
    def from_dem_problem(cls, problem):
        """Create a prepared analysis from a refactored COMPAS DEM problem.

        In the current ``compas_dem`` API the model is a transient reference
        on ``Problem``. When a complete ``compas_dem.models.Analysis`` is
        deserialised, it restores that reference before the problem is solved.
        """
        return cls.from_blockmodel(problem.model, problem)
