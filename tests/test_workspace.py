import subprocess
from types import SimpleNamespace

import pytest
from compas.datastructures import Mesh
from compas_dem.problem import BoundaryConditionGroup

from compas_3dec.solver import ThreeDECBlockMaterial
from compas_3dec.solver import ThreeDECContactProperties
from compas_3dec.solver import ThreeDECAnalysis
from compas_3dec.solver import ThreeDECEntityMap
from compas_3dec.solver import ThreeDECRawResults
from compas_3dec.solver import ThreeDECStage
from compas_3dec import ThreeDECSolver
from compas_3dec.solver import ThreeDECStagePlan
from compas_3dec.solver.engine import _capacity_stage
from compas_3dec.solver.engine import _last_equilibrium_stage
from compas_3dec.solver.io import ThreeDECWorkspace


def make_gravity_analysis():
    mesh = Mesh.from_vertices_and_faces(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        [
            [0, 2, 1],
            [0, 1, 3],
            [1, 2, 3],
            [2, 0, 3],
        ],
    )
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=0,
        element_guid="block-0",
        region=0,
        vertices=[(vertex, mesh.vertex_coordinates(vertex)) for vertex in mesh.vertices()],
    )
    return ThreeDECAnalysis(
        name="gravity",
        model_id="model",
        problem_id="problem",
        blocks=[
            {
                "node": 0,
                "element_guid": "block-0",
                "region": 0,
                "name": "block",
                "geometry": mesh,
                "material": ThreeDECBlockMaterial(density=1800),
                "is_support": True,
            }
        ],
        supports=[0],
        boundary_conditions=[],
        contact_properties=ThreeDECContactProperties(
            stiffness_normal=1e9,
            stiffness_shear=5e8,
            friction=35.0,
        ),
        entity_map=mapping,
        stages=[
            ThreeDECStage(
                name="gravity",
                kind="gravity",
                gravity=9.81,
                options={"gravity_steps": 10, "ratio": 1e-5, "ratio_keyword": "ratio-local", "time": 1.0},
            )
        ],
    )


def test_solver_reports_elapsed_time_and_equilibrium(capsys):
    solver = ThreeDECSolver()
    results = ThreeDECRawResults(
        metadata={
            "ratio_local": 8.0e-6,
            "target_ratio": 1.0e-5,
            "converged": True,
            "elapsed_seconds": 12.3456,
        }
    )

    assert solver.report_solve_summary(results) is True
    output = capsys.readouterr().out
    assert "3DEC execution time = 12.346 seconds" in output
    assert "Equilibrium reached" in output
    assert "Solve ratio = 8e-06" in output
    assert "Target solve ratio = 1e-05" in output


def test_solver_records_timeout_as_failed_run(tmp_path, monkeypatch):
    executable = tmp_path / "3dec-console.exe"
    executable.touch()
    runs = tmp_path / "runs"
    solver = ThreeDECSolver(executable=executable, workspace=runs, timeout=1)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired([str(executable), "analysis.dat"], 1)

    monkeypatch.setattr(solver, "_run_process", timeout)

    with pytest.raises(subprocess.TimeoutExpired):
        solver.solve(make_gravity_analysis(), run_id="timeout-test")

    manifest = ThreeDECWorkspace(runs / "timeout-test").read_manifest()
    assert manifest["status"] == "failed"
    assert manifest["failure"] == "timeout"
    assert manifest["timeout"] == 1


def test_prepare_run_writes_isolated_serialisable_workspace(tmp_path):
    analysis = make_gravity_analysis()
    solver = ThreeDECSolver(
        version="9.0",
        workspace=tmp_path,
    )

    workspace = solver.prepare_run(analysis, run_id="gravity-test")

    assert workspace.path == tmp_path / "gravity-test"
    assert workspace.file("analysis.json").is_file()
    assert workspace.file("stages.json").is_file()
    assert workspace.file("geometry.dat").is_file()
    assert workspace.file("analysis.dat").is_file()

    geometry = workspace.file("geometry.dat").read_text(encoding="utf-8")
    deck = workspace.file("analysis.dat").read_text(encoding="utf-8")
    manifest = workspace.read_manifest()

    assert "r=0" in geometry
    assert "block.gp.id(gp)" in deck
    assert "model precision 15" in deck
    assert "model gravity 0 0 -9.81" in deck
    assert manifest["status"] == "prepared"
    assert manifest["files"]["deck"] == "analysis.dat"


def test_default_run_directory_uses_analysis_name_and_timestamp(tmp_path):
    analysis = make_gravity_analysis()
    analysis.name = "Arch gravity test"
    solver = ThreeDECSolver(version="9.0", workspace=tmp_path)

    workspace = solver.prepare_run(analysis)

    assert workspace.run_id.startswith("Arch_gravity_test_")
    assert workspace.path.name == workspace.run_id


@pytest.mark.parametrize("run_id", ["../outside", "..\\outside", "C:\\outside", "bad:name"])
def test_explicit_run_id_cannot_escape_workspace(tmp_path, run_id):
    with pytest.raises(ValueError, match="run_id"):
        ThreeDECWorkspace.create(root=tmp_path, run_id=run_id)


def test_compas_dem_point_loads_use_direct_load_schema():
    analysis = make_gravity_analysis()
    analysis.stages = []
    analysis.boundary_conditions = [
        SimpleNamespace(
            guid="boundary-condition",
            g=9.81,
            body_forces=[],
            point_loads=[
                {"block_index": 0, "force": [0, 0, -2000]},
                {"block_index": 0, "force": [3000, 0, 0], "point": [0.0, 0.0, 1.0]},
            ],
            surface_loads=[],
            displacements=[],
        )
    ]

    loads = ThreeDECStagePlan.from_analysis(analysis).stage("loads").point_loads

    assert loads[0]["kind"] == "centroid"
    assert loads[0]["magnitude"] == 2000
    assert loads[0]["direction"] == [0.0, 0.0, -1.0]
    assert loads[1]["kind"] == "sphere"
    assert loads[1]["point"] == [0.0, 0.0, 1.0]


def test_compas_dem_loads_require_gravity():
    analysis = make_gravity_analysis()
    analysis.stages = []
    boundary_condition = SimpleNamespace(
        guid="live-load",
        g=None,
        body_forces=[],
        point_loads=[{"block_index": 0, "force": [0, 0, -2000]}],
        surface_loads=[],
        displacements=[],
    )
    analysis.boundary_conditions = [boundary_condition]

    with pytest.raises(ValueError, match="require exactly one gravity stage"):
        ThreeDECStagePlan.from_analysis(analysis)


def test_final_stage_controls_convergence_and_capacity_detection():
    load = {"capacity": False}
    capacity_load = {"capacity": True}
    plan = ThreeDECStagePlan(
        stages=[
            ThreeDECStage(name="initialization", kind="initialization"),
            ThreeDECStage(name="gravity", kind="gravity", options={"ratio": 1e-4}),
            ThreeDECStage(name="loads", kind="loads", point_loads=[load], options={"ratio": 1e-5}),
            ThreeDECStage(name="displacements", kind="displacements", displacements=[{"capacity": False}], options={"ratio": 1e-6}),
            ThreeDECStage(name="loads-2", kind="loads", point_loads=[capacity_load], options={"ratio": 1e-7}),
        ]
    )

    assert _last_equilibrium_stage(plan).name == "loads-2"
    stage, kind = _capacity_stage(plan)
    assert stage.name == "loads-2"
    assert kind == "load"


def test_compas_dem_groups_become_sequential_stages_in_registered_order():
    analysis = make_gravity_analysis()
    analysis.stages = []

    gravity = BoundaryConditionGroup(name="Gravity")
    gravity.add_gravity(g=9.81)
    settlement = BoundaryConditionGroup(name="Support settlement")
    settlement.add_displacement(block_index=0, dx=0.001, dy=None, dz=None)
    live_load = BoundaryConditionGroup(name="Live load")
    live_load.add_point_load(block_index=0, force=[0, 0, -2000])
    analysis.boundary_conditions = [gravity, settlement, live_load]

    plan = ThreeDECStagePlan.from_analysis(analysis)

    assert [stage.kind for stage in plan.stages] == ["initialization", "gravity", "displacements", "loads"]
    assert [stage.name for stage in plan.stages] == [
        "initialization",
        "gravity",
        "support-settlement-displacements",
        "live-load-loads",
    ]
    assert plan.stages[2].source_boundary_conditions == [str(settlement.guid)]
    assert plan.stages[3].source_boundary_conditions == [str(live_load.guid)]


def test_compas_dem_configured_load_groups_share_one_stage():
    analysis = make_gravity_analysis()
    analysis.stages = []

    gravity = BoundaryConditionGroup(name="Gravity")
    gravity.add_gravity(g=9.81)
    dead = BoundaryConditionGroup(name="Dead load")
    dead.add_point_load(block_index=0, force=[0, 0, -1000])
    live = BoundaryConditionGroup(name="Live load")
    live.add_point_load(block_index=0, force=[0, 0, -2000])
    analysis.boundary_conditions = [gravity, dead, live]
    analysis.solver_configuration = {
        "name": "3DEC",
        "parameters": {"stages": [["Gravity"], ["Dead load", "Live load"]]},
    }

    plan = ThreeDECStagePlan.from_analysis(analysis)

    assert [stage.kind for stage in plan.stages] == ["initialization", "gravity", "loads"]
    assert len(plan.stages[2].point_loads) == 2
    assert plan.stages[2].source_boundary_conditions == [str(dead.guid), str(live.guid)]


def test_prepare_run_indexes_compas_dem_load_stage(tmp_path):
    """A DEM-derived load stage must also exist in the result-state index."""
    analysis = make_gravity_analysis()
    analysis.stages = []
    boundary_condition = BoundaryConditionGroup(name="gravity-and-load")
    boundary_condition.add_gravity(g=9.81)
    boundary_condition.add_point_load(block_index=0, force=[0, 0, -2000])
    analysis.boundary_conditions = [boundary_condition]

    workspace = ThreeDECSolver(version="7.0", workspace=tmp_path).prepare_run(
        analysis,
        run_id="dem-load",
    )
    manifest = workspace.read_manifest()

    assert workspace.file("loads.dat").is_file()
    assert "gravity-and-load-loads" in manifest["result_states"]
    assert manifest["result_states"]["gravity-and-load-loads"]["source_state"] == "gravity"
