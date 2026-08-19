from types import SimpleNamespace

from compas.datastructures import Mesh

from compas_3dec.solver import ThreeDECBlockMaterial
from compas_3dec.solver import ThreeDECContactProperties
from compas_3dec.solver import ThreeDECAnalysis
from compas_3dec.solver import ThreeDECEntityMap
from compas_3dec.solver import ThreeDECRawResults
from compas_3dec.solver import ThreeDECStage
from compas_3dec import ThreeDECSolver
from compas_3dec.solver import ThreeDECStagePlan


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


def test_prepare_run_writes_isolated_serializable_workspace(tmp_path):
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


def test_compas_dem_point_loads_use_direct_load_schema():
    analysis = make_gravity_analysis()
    analysis.stages = []
    analysis.boundary_conditions = [
        SimpleNamespace(
            guid="boundary-condition",
            g=None,
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
