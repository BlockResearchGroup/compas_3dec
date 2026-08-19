from uuid import uuid4

import pytest
from compas.datastructures import Mesh
from compas_dem.problem import Problem
from compas_dem.problem import Solver

from compas_3dec.solver import ThreeDECAnalysis
from compas_3dec import ThreeDECAnalysisBuilder
from compas_3dec import ThreeDECSolver


class FakeGraph:
    def __init__(self, edges=None, contacts=None):
        self._edges = list(edges or [])
        self._contacts = dict(contacts or {})

    def edges(self):
        return iter(self._edges)

    def edge_attribute(self, edge, name):
        assert name == "contacts"
        return self._contacts.get(tuple(edge))


class FakeElement:
    def __init__(self, node, x):
        self.guid = uuid4()
        self.graphnode = node
        self.name = "block-{}".format(node)
        self.modelgeometry = Mesh.from_vertices_and_faces(
            [
                [x, 0.0, 0.0],
                [x + 1.0, 0.0, 0.0],
                [x, 1.0, 0.0],
            ],
            [[0, 1, 2]],
        )
        self.material = None
        self.is_support = node == 0


class FakeModel:
    def __init__(self):
        self.guid = uuid4()
        self._elements = [FakeElement(0, 0.0), FakeElement(1, 1.0)]
        self.graph = FakeGraph(edges=[(0, 1)])

    def elements(self):
        return iter(self._elements)


def make_problem(model):
    problem = Problem(model, name="gravity")
    boundary_condition = problem.add_boundary_condition("gravity")
    boundary_condition.add_gravity()
    solver = Solver()
    solver.name = "3DEC"
    solver.parameters = {
        "version": "9.0",
        "ratio": 1e-6,
        "executable": r"C:\Program Files\Itasca\3DEC900.exe",
        "workspace": r"C:\temporary\run",
    }
    problem.set_solver(solver)
    return problem


def test_from_blockmodel_preserves_graph_node_as_region():
    model = FakeModel()
    problem = make_problem(model)

    analysis = ThreeDECAnalysis.from_blockmodel(model, problem)

    assert analysis.model_id == str(model.guid)
    assert analysis.problem_id == str(problem.guid)
    assert analysis.entity_map.region_for_node(0) == 0
    assert analysis.entity_map.region_for_node(1) == 1
    assert analysis.entity_map.edge_for_regions(1, 0) == (0, 1)
    assert analysis.blocks[0]["is_support"] is True
    assert analysis.blocks[0]["group"] == "supports"
    assert analysis.blocks[1]["group"] == "block"
    assert analysis.supports == [0]
    assert analysis.solver_configuration == {
        "name": "3DEC",
        "parameters": {"version": "9.0", "ratio": 1e-6},
    }


def test_from_dem_problem_uses_transient_problem_model():
    model = FakeModel()
    problem = make_problem(model)

    analysis = ThreeDECAnalysis.from_dem_problem(problem)

    assert analysis.model_id == str(model.guid)
    assert analysis.problem_id == str(problem.guid)


def test_analysis_builder_reads_complete_compas_dem_problem():
    model = FakeModel()
    problem = make_problem(model)

    analysis = ThreeDECAnalysisBuilder.from_dem_problem(problem).build()

    assert analysis.model_id == str(model.guid)
    assert analysis.problem_id == str(problem.guid)
    assert analysis.supports == [0]
    assert len(analysis.boundary_conditions) == 1
    assert analysis.entity_map.region_for_node(1) == 1
    assert analysis.entity_map.edge_for_regions(1, 0) == (0, 1)
    assert analysis.solver_configuration == {
        "name": "3DEC",
        "parameters": {"version": "9.0", "ratio": 1e-6},
    }


def test_solver_prepares_compas_dem_problem():
    model = FakeModel()
    problem = make_problem(model)

    analysis = ThreeDECSolver().prepare(problem)

    assert isinstance(analysis, ThreeDECAnalysis)
    assert analysis.model_id == str(model.guid)
    assert analysis.problem_id == str(problem.guid)


def test_dem_problem_uses_global_contact_properties_only():
    model = FakeModel()
    problem = make_problem(model)
    builder = ThreeDECAnalysisBuilder.from_dem_problem(problem)
    builder.add_group("left", nodes=[0])
    builder.add_group("right", nodes=[1])

    with pytest.raises(ValueError, match="only for direct"):
        builder.set_contact_properties_between_groups("left", "right")


def test_analysis_builder_reads_bare_blockmodel():
    model = FakeModel()
    builder = ThreeDECAnalysisBuilder.from_blockmodel(model)
    builder.set_material(2500, 25e9, 0.2)
    builder.set_contact_properties()

    analysis = builder.build()

    assert analysis.model_id == str(model.guid)
    assert analysis.supports == [0]
    assert analysis.entity_map.edge_for_regions(1, 0) == (0, 1)


def test_from_blockmodel_rejects_problem_for_another_model():
    model = FakeModel()
    problem = make_problem(model)
    problem.model_id = str(uuid4())

    with pytest.raises(ValueError, match="does not match model GUID"):
        ThreeDECAnalysis.from_blockmodel(model, problem)
