import os

import pytest


pytestmark = pytest.mark.skipif(
    not os.getenv("COMPAS_3DEC_EXECUTABLE"),
    reason="Set COMPAS_3DEC_EXECUTABLE to run the real external integration smoke tests.",
)


def _staged_arch_problem(workspace):
    """Build a small gravity-load-displacement problem through COMPAS DEM."""
    pytest.importorskip("compas_dem")

    from compas_dem.material import GenericMaterial
    from compas_dem.models import BlockModel
    from compas_dem.problem import Problem
    from compas_dem.problem import Solver
    from compas_dem.templates import ArchTemplate

    arch = ArchTemplate(
        rise=0.5,
        span=5.0,
        thickness=0.3,
        depth=0.3,
        n=10,
    )
    model = BlockModel()
    nodes = [model.add_block_from_mesh(mesh) for mesh in arch.blocks()]
    model.add_supports([nodes[0], nodes[-1]])

    material = GenericMaterial(
        Ecm=25e9,
        density=2500,
        poisson=0.2,
        name="Smoke-test masonry",
    )
    model.add_material(material)
    model.assign_material(material, elements=list(model.elements()))

    problem = Problem(model, name="Staged 3DEC smoke")
    gravity = problem.add_boundary_condition("Gravity")
    gravity.add_gravity()

    load = problem.add_boundary_condition("Load")
    problem.add_point_load_at_centroid(
        block_index=nodes[len(nodes) // 2],
        force=[0.0, 0.0, -500.0],
        boundary_condition=load,
    )

    settlement = problem.add_boundary_condition("Settlement")
    problem.add_displacement(
        block_index=nodes[-1],
        displacement=[-1e-5, None, None],
        boundary_condition=settlement,
    )

    stages = [["Gravity"], ["Load"], ["Settlement"]]
    problem.set_solve_order([name for stage in stages for name in stage])
    problem.set_contact_model("MohrCoulomb", phi=35.0)
    problem.set_joint_model(kn=1e9, kt=5e8)
    problem.set_solver(
        Solver.ThreeDEC(
            version=os.getenv("COMPAS_3DEC_VERSION", "7.0"),
            executable=os.environ["COMPAS_3DEC_EXECUTABLE"],
            workspace=str(workspace),
            gravity_steps=5,
            stages=stages,
            suppress_output=True,
            timeout=300,
        )
    )
    return model, nodes, problem


def _assert_staged_results(results, nodes):
    """Verify that the final compact result contains every imposed stage."""
    from compas_dem.problem import Results

    assert isinstance(results, Results)
    assert results.metadata["solver"] == "3DEC"
    assert results.metadata["converged"] is True
    assert results.metadata["result_state"] == "final"
    assert results.metadata["applied_loads"][0]["force"] == [0.0, 0.0, -500.0]
    assert results.metadata["prescribed_displacements"][0]["displacement"] == [-1e-5, 0.0, 0.0]
    assert set(results.nodes()) == set(nodes)
    assert list(results.edges())


def test_compas_dem_staged_real_smoke(tmp_path):
    """Run gravity, a point load, and a displacement through COMPAS DEM."""
    _, nodes, problem = _staged_arch_problem(tmp_path / "runs")

    results = problem.solve()

    _assert_staged_results(results, nodes)


def test_compas_masonry_staged_real_smoke(tmp_path):
    """Run and persist the staged solve through a headless masonry session."""
    pytest.importorskip("compas_masonry")

    from compas_dem.models import Analysis
    from compas_masonry.session import MasonrySession

    model, nodes, problem = _staged_arch_problem(tmp_path / "runs")
    analysis = Analysis(model=model, name="COMPAS-Masonry smoke")
    analysis.add_problem(problem)

    session_root = tmp_path / "session"
    session = MasonrySession(basedir=session_root, name="COMPAS-Masonry smoke")
    session["analysis"] = analysis

    active_problem = session.problems[problem.name]
    assert MasonrySession.solver_of(active_problem).name == "3DEC"

    results = active_problem.solve()
    _assert_staged_results(results, nodes)

    result_key = "3DEC_staged_smoke"
    session["results"] = {problem.name: {result_key: results}}

    reloaded = MasonrySession(basedir=session_root, name="COMPAS-Masonry smoke")
    reloaded_problem = reloaded.problems[problem.name]
    reloaded_results = reloaded.get("results")[problem.name][result_key]

    assert MasonrySession.solver_of(reloaded_problem).name == "3DEC"
    assert reloaded_results.metadata["run_id"] == results.metadata["run_id"]
    _assert_staged_results(reloaded_results, nodes)
