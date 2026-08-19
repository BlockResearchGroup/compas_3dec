import compas
import pytest
from compas.datastructures import Mesh

from compas_3dec.solver import ThreeDECAnalysis
from compas_3dec.solver import ThreeDECStagePlan
from compas_3dec import ThreeDECSolver
from compas_3dec.solver import ThreeDECBlockMaterial
from compas_3dec import ThreeDECAnalysisBuilder
from compas_3dec.rhino import build_visualisation


def tetrahedron(x=0.0):
    return Mesh.from_vertices_and_faces(
        [
            [x + 0.0, 0.0, 0.0],
            [x + 1.0, 0.0, 0.0],
            [x + 0.0, 1.0, 0.0],
            [x + 0.0, 0.0, 1.0],
        ],
        [[0, 2, 1], [0, 1, 3], [1, 2, 3], [2, 0, 3]],
    )


def make_direct_analysis():
    builder = ThreeDECAnalysisBuilder.from_meshes(
        [tetrahedron(0.0), tetrahedron(1.0)],
        name="direct",
    )
    builder.set_material(density=1800, young_modulus=25e9, poisson_ratio=0.2)
    builder.set_supports([0])
    builder.set_contact_properties()
    builder.add_gravity(g=9.81, gravity_steps=5)
    return builder.build()


def test_direct_builder_creates_portable_analysis_without_dem_model():
    analysis = make_direct_analysis()

    assert isinstance(analysis, ThreeDECAnalysis)
    assert analysis.supports == [0]
    assert [block["node"] for block in analysis.blocks] == [0, 1]
    assert analysis.blocks[0]["material"].density == 1800
    assert analysis.blocks[0]["material"].E == 25e9
    assert analysis.blocks[0]["material"].poisson == 0.2
    assert analysis.blocks[0]["material"].shear_modulus == pytest.approx(25e9 / 2.4)
    assert analysis.contact_properties.friction == 35.0
    assert [stage.kind for stage in analysis.stages] == ["gravity"]
    assert analysis.boundary_conditions == []

    restored = compas.json_loads(compas.json_dumps(analysis))
    assert isinstance(restored, ThreeDECAnalysis)
    assert restored.blocks[1]["geometry"].number_of_vertices() == 4
    assert restored.contact_properties.stiffness_normal == 100e9
    assert restored.contact_properties.stiffness_shear == 70e9


def test_direct_stage_plan_adds_initialisation():
    plan = ThreeDECStagePlan.from_analysis(make_direct_analysis())

    assert [stage.kind for stage in plan.stages] == ["initialization", "gravity"]
    assert plan.stage("gravity").options["gravity_steps"] == 5


def test_calculate_joint_stiffness_for_one_material():
    material = ThreeDECBlockMaterial(2500, 30e9, 0.25)

    kn, kt = ThreeDECAnalysisBuilder.calculate_joint_stiffness_one_material(
        material,
        block_height=0.2,
        block_length=0.4,
        reduction_factor=10.0,
    )

    assert kn == pytest.approx(11.25e9)
    assert kt == pytest.approx(4.5e9)


def test_calculate_joint_stiffness_for_two_materials():
    stone = ThreeDECBlockMaterial(2500, 30e9, 0.25)
    mortar = ThreeDECBlockMaterial(1800, 10e9, 0.20)

    kn, kt = ThreeDECAnalysisBuilder.calculate_joint_stiffness_two_materials(
        block_material=stone,
        interface_material=mortar,
        block_height=0.2,
        interface_thickness=0.01,
        reduction_factor=2.0,
    )

    assert kn == pytest.approx((30e9 * 10e9) / (0.2 * 10e9 + 0.01 * 30e9) / 2.0)
    assert kt == pytest.approx((12e9 * (10e9 / 2.4)) / (0.2 * (10e9 / 2.4) + 0.01 * 12e9) / 2.0)


def test_direct_analysis_generates_gravity_workspace(tmp_path):
    analysis = make_direct_analysis()
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)

    workspace = solver.prepare_run(analysis, run_id="direct-test")
    deck = workspace.file("analysis.dat").read_text(encoding="utf-8")
    assert "block property density 1800 range group 'block'" in deck
    assert "stiffness-normal 100000000000" in deck
    assert "stiffness-shear 70000000000" in deck
    assert "friction 35" in deck
    assert "block fix range region 0" in deck
    assert deck.count("model gravity") == 5
    assert "model save './gravity.sav' compress" in deck


def test_synchronized_sphere_and_centroid_point_loads(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    builder.add_point_load(
        magnitude=10000,
        direction=[0, 0, -1],
        steps=10,
        point=[1.0, 0.0, 1.0],
        radius=0.02,
        block=1,
        distribution_count=2,
        save_steps=True,
    )
    builder.add_centroid_load(
        magnitude=20000,
        direction=[1, 0, 0],
        steps=20,
        blocks=[1],
        save_steps=True,
    )
    analysis = builder.build()
    restored = compas.json_loads(compas.json_dumps(analysis))
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(restored, run_id="point-load-test")
    manifest = workspace.read_manifest()
    gravity_deck = workspace.file("analysis.dat").read_text(encoding="utf-8")
    deck = workspace.file("loads.dat").read_text(encoding="utf-8")

    assert "; Load step " not in gravity_deck
    assert "model save './gravity.sav' compress" in gravity_deck
    assert "results-gravity.txt" in gravity_deck
    assert {"initial", "gravity", "final"}.issubset(manifest["result_states"])
    assert manifest["result_states"]["load-step-0005"]["step"] == 5
    assert manifest["result_states"]["load-step-0005"]["applied_loads"][0]["magnitude"] == 5000
    assert manifest["result_states"]["final"]["applied_loads"][1]["magnitude"] == 20000
    assert deck.count("; Load step ") == 20
    assert deck.count("block gridpoint apply force-x") == 10
    assert deck.count("force-z -500") == 10
    assert "force-z -5000" not in deck
    assert "range sphere c 1 0 1 r 0.02 region 1" in deck
    assert "block.force.app(ib) = vector(20000,0,0)" in deck
    assert deck.count("model solve ratio-local 1e-05 or cycles 15000") >= 20
    assert deck.count("system.command('exit')") == 20
    assert deck.count("program log-file 'results-final.txt'") >= 20
    assert deck.count("program log on truncate") >= 20
    assert deck.startswith("; Generated by compas_3dec: point-load stage\nmodel restore './gravity.sav'")
    assert "block mechanical damping global" in deck
    assert "load-final.sav" in deck


def test_centroid_load_applies_the_magnitude_to_each_selected_block(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    builder.add_centroid_load(
        magnitude=12000,
        direction=[0, 0, -2],
        steps=1,
        blocks=[0, 1],
        cycles=500,
        solve_time=None,
        save_steps=False,
    )
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(builder.build(), run_id="centroid-load-test")
    deck = workspace.file("loads.dat").read_text(encoding="utf-8")

    assert deck.count("block.force.app(ib) = vector(0,0,-12000)") == 2
    assert "model solve ratio-local 1e-05 or cycles 500" in deck


def test_face_stress_is_incremented_and_synchronized_with_point_loads(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    load = builder.add_face_stress(
        block=1,
        face=0,
        stress=[0, 0, -12000, 1000, 2000, 3000],
        steps=3,
    )
    builder.add_point_load(
        magnitude=1000,
        direction=[0, 0, -1],
        steps=2,
        point=[1, 0, 0],
        radius=0.01,
        block=1,
        distribution_count=1,
    )
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(builder.build(), run_id="surface-stress-test")
    deck = workspace.file("loads.dat").read_text(encoding="utf-8")
    manifest = workspace.read_manifest()

    assert load["traction"] == pytest.approx([-3000, -2000, 12000])
    assert deck.count("block face apply stress") == 3
    # 3DEC tensor order is xx, yy, zz, xy, xz, yz.
    assert "block face apply stress 0 0 -4000 333.333333333 1000 666.666666667" in deck
    assert deck.count("; Load step ") == 3
    assert any(item["kind"] == "surface_stress" for item in manifest["result_states"]["final"]["applied_loads"])


def test_surface_traction_generates_tensor_that_recovers_traction():
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    load = builder.add_surface_load(block=1, face=0, load=[100, 200, -300], steps=2)
    xx, yy, zz, xy, yz, zx = load["stress"]
    nx, ny, nz = load["face_normal"]
    recovered = [
        xx * nx + xy * ny + zx * nz,
        xy * nx + yy * ny + yz * nz,
        zx * nx + yz * ny + zz * nz,
    ]

    assert recovered == pytest.approx([100, 200, -300])


def test_surface_load_label_reports_traction_in_kn_per_square_metre():
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    load = builder.add_surface_load(block=1, face=0, load=[0, 0, -1000], steps=1)
    analysis = builder.build()

    class Results:
        blocks = []
        contacts = []
        metadata = {
            "result_state": "final",
            "applied_loads": [
                {
                    **load,
                    "force": [value * load["face_area"] for value in load["traction"]],
                }
            ],
        }

    visual = build_visualisation(analysis, Results())

    assert {label["text"] for label in visual["applied_load_labels"]} == {"1.0 kN/m²"}
    assert len(visual["applied_load_labels"]) == 1
    assert list(visual["applied_load_labels"][0]["point"]) == pytest.approx(load["face_center"])


def test_displacement_stage_restores_gravity_and_equilibrates_each_increment(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    builder.add_displacement(
        blocks=[0],
        magnitude=0.003,
        direction=[-1, 0, 0],
        steps=3,
        motion_time=1.0,
        equilibrium_cycles=12000,
    )
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(builder.build(), run_id="displacement-test")
    deck = workspace.file("displacements.dat").read_text(encoding="utf-8")
    manifest = workspace.read_manifest()

    assert deck.startswith("; Generated by compas_3dec: displacement stage\nmodel restore './gravity.sav'")
    assert "block mechanical damping local" in deck
    assert deck.count("; Displacement step ") == 3
    assert deck.count("math.ceil(1 / mech.timestep)") == 3
    assert deck.count("block apply velocity-x [-0.001/compas_3dec_displacement_time_") == 3
    assert deck.count("block apply velocity-x 0 range region 0") == 3
    assert deck.count("model solve ratio-local 1e-05 or cycles 12000") == 3
    assert manifest["files"]["displacement_deck"] == "displacements.dat"
    assert manifest["result_states"]["final"]["save"] == "displacement-final.sav"
    assert manifest["result_states"]["displacement-step-0002"]["prescribed_displacements"][0]["magnitude"] == pytest.approx(0.002)


def test_multiple_displacements_are_synchronized_and_load_state_is_restored(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    builder.add_point_load(
        magnitude=1000,
        direction=[0, 0, -1],
        steps=2,
        point=[1, 0, 0],
        radius=0.01,
        block=1,
        distribution_count=1,
    )
    builder.add_displacement([0], 0.002, [1, 0, 0], 2)
    builder.add_displacement([1], 0.006, [0, 0, -1], 3)
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(builder.build(), run_id="combined-displacement-test")
    deck = workspace.file("displacements.dat").read_text(encoding="utf-8")
    load_deck = workspace.file("loads.dat").read_text(encoding="utf-8")
    manifest = workspace.read_manifest()

    assert "model restore './load-final.sav'" in deck
    assert deck.count("; Displacement step ") == 3
    assert deck.count("block apply velocity-x [0.001/compas_3dec_displacement_time_") == 2
    assert deck.count("block apply velocity-z [-0.002/compas_3dec_displacement_time_") == 3
    assert "results-load-final.txt" in load_deck
    assert manifest["result_states"]["loads"]["save"] == "load-final.sav"
    assert manifest["result_states"]["final"]["source_state"] == "loads"


def test_boundary_condition_phases_follow_builder_call_order(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    builder.add_centroid_load(1000, [0, 0, -1], 2, [1])
    builder.add_displacement([0], 0.001, [1, 0, 0], 1)
    builder.add_centroid_load(500, [0, 0, -1], 1, [1])
    analysis = builder.build()

    assert [stage.kind for stage in analysis.stages] == [
        "gravity",
        "loads",
        "displacements",
        "loads",
    ]
    assert [stage.name for stage in analysis.stages] == [
        "gravity",
        "loads",
        "displacements",
        "loads-2",
    ]

    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(analysis, run_id="ordered-stages-test")
    manifest = workspace.read_manifest()

    assert manifest["files"]["stage_decks"] == [
        "loads.dat",
        "displacements.dat",
        "loads-2.dat",
    ]
    assert "model restore './gravity.sav'" in workspace.file("loads.dat").read_text()
    assert "model restore './load-final.sav'" in workspace.file("displacements.dat").read_text()
    assert "model restore './displacement-final.sav'" in workspace.file("loads-2.dat").read_text()
    assert manifest["result_states"]["final"]["save"] == "load-2-final.sav"


def test_user_can_split_consecutive_loads_into_sequential_phases(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    builder.add_centroid_load(1000, [0, 0, -1], 1, [1])
    builder.start_new_phase()
    builder.add_centroid_load(500, [1, 0, 0], 1, [1])

    analysis = builder.build()
    assert [stage.name for stage in analysis.stages] == [
        "gravity",
        "loads",
        "loads-2",
    ]

    workspace = ThreeDECSolver(
        version="7.0",
        workspace=tmp_path,
    ).prepare_run(analysis, run_id="sequential-loads-test")
    assert "model restore './load-final.sav'" in workspace.file("loads-2.dat").read_text()


def test_point_load_automatically_counts_vertices_and_batch_adds_points():
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    load = builder.add_point_load(
        magnitude=1000,
        direction=[0, 0, -1],
        steps=2,
        point=[1.0, 0.0, 0.0],
        radius=1e-6,
    )
    loads = builder.add_point_loads(
        points=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
        magnitude=2000,
        direction=[0, -1, 0],
        steps=4,
        radius=1e-6,
    )

    # The shared coordinate x=1 belongs to both rigid blocks and therefore
    # represents two distinct 3DEC gridpoints.
    assert load["distribution_count"] == 2
    assert len(loads) == 2
    assert [item["distribution_count"] for item in loads] == [1, 1]


def test_point_load_capacity_uses_constant_increments_and_collapse_guard(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    load = builder.add_load_capacity(
        magnitude_increment=750,
        direction=[0, 0, -1],
        point=[1, 0, 0],
        radius=0.01,
        block=1,
        distribution_count=1,
        max_steps=4,
    )
    workspace = ThreeDECSolver(version="7.0", workspace=tmp_path).prepare_run(builder.build(), run_id="point-capacity-test")
    deck = workspace.file("loads.dat").read_text(encoding="utf-8")
    states = workspace.read_manifest()["result_states"]

    assert load["capacity"] is True
    assert load["magnitude"] == 3000
    assert deck.count("force-z -750") == 4
    assert deck.count("system.command('exit')") == 4
    assert states["load-step-0003"]["applied_loads"][0]["magnitude"] == 2250
    assert states["load-step-0003"]["applied_loads"][0]["capacity"] is True


def test_surface_load_capacity_uses_traction_increment(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    load = builder.add_surface_load_capacity(
        block=1,
        face=0,
        load_increment=[0, 0, -1000],
        max_steps=3,
    )
    workspace = ThreeDECSolver(version="7.0", workspace=tmp_path).prepare_run(builder.build(), run_id="surface-capacity-test")
    deck = workspace.file("loads.dat").read_text(encoding="utf-8")

    assert load["traction"] == pytest.approx([0, 0, -3000])
    assert load["capacity_increment"] == [0, 0, -1000]
    assert deck.count("block face apply stress") == 3
    assert deck.count("system.command('exit')") == 3


def test_displacement_capacity_uses_cumulative_increment(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_analysis(make_direct_analysis())
    displacement = builder.add_displacement_capacity(
        blocks=[0],
        magnitude_increment=0.0005,
        direction=[1, 0, 0],
        max_steps=5,
    )
    workspace = ThreeDECSolver(version="7.0", workspace=tmp_path).prepare_run(builder.build(), run_id="displacement-capacity-test")
    deck = workspace.file("displacements.dat").read_text(encoding="utf-8")
    states = workspace.read_manifest()["result_states"]

    assert displacement["magnitude"] == pytest.approx(0.0025)
    assert deck.count("block apply velocity-x [0.0005/compas_3dec_displacement_time_") == 5
    assert deck.count("system.command('exit')") == 5
    assert states["displacement-step-0004"]["prescribed_displacements"][0]["magnitude"] == pytest.approx(0.002)


def test_direct_builder_validates_required_configuration():
    builder = ThreeDECAnalysisBuilder.from_meshes([tetrahedron()])

    with pytest.raises(ValueError, match="No material"):
        builder.build()

    builder.set_material(density=1800, young_modulus=25e9, poisson_ratio=0.2)
    with pytest.raises(ValueError, match="contact properties"):
        builder.build()


def test_direct_interfaces_are_optional_and_serialisable():
    builder = ThreeDECAnalysisBuilder.from_meshes([tetrahedron(0.0), tetrahedron(1.0)])
    builder.set_material(density=1800, young_modulus=25e9, poisson_ratio=0.2)
    builder.set_supports([0])
    builder.set_contact_properties(kn=1e9, kt=5e8, friction=35.0)
    builder.add_gravity()
    builder.add_interface(0, 1)

    analysis = builder.build()
    restored = compas.json_loads(compas.json_dumps(analysis))

    assert restored.entity_map.edge_for_regions(1, 0) == (0, 1)
    assert restored.entity_map.edges[0]["source"] == "direct"


def test_block_has_exactly_one_group_and_reassignment_replaces_it():
    builder = ThreeDECAnalysisBuilder.from_meshes([tetrahedron(0.0), tetrahedron(1.0)])
    builder.add_group("arch", nodes=[0, 1])
    builder.add_group("abutment", nodes=[0])
    builder.set_material(2500, 25e9, 0.2, group="arch")
    builder.set_material(2600, 30e9, 0.2, group="abutment")
    builder.set_contact_properties()

    analysis = builder.build()

    assert analysis.blocks[0]["group"] == "abutment"
    assert analysis.blocks[1]["group"] == "arch"


def test_contact_properties_between_groups_render_existing_and_future_rules(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_meshes([tetrahedron(0.0), tetrahedron(1.0)])
    builder.add_group("arch", nodes=[0])
    builder.add_group("abutment", nodes=[1])
    builder.set_material(2500, 25e9, 0.2, group="arch")
    builder.set_material(2600, 30e9, 0.2, group="abutment")
    builder.set_contact_properties(kn=100e9, kt=70e9, friction=35)
    builder.set_contact_properties_between_groups(
        "arch",
        "abutment",
        kn=50e9,
        kt=30e9,
        friction=25,
    )

    analysis = builder.build()
    restored = compas.json_loads(compas.json_dumps(analysis))
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(restored, run_id="group-contact-test")
    geometry = workspace.file("geometry.dat").read_text(encoding="utf-8")
    deck = workspace.file("analysis.dat").read_text(encoding="utf-8")

    assert "group 'arch'" in geometry
    assert "group 'abutment'" in geometry
    selector = "range group-intersection 'abutment' 'arch'"
    assert "block contact property stiffness-normal 50000000000" in deck
    assert selector in deck
    assert "block contact material-table add jmodel mohr property" in deck
    assert len(restored.contact_property_overrides) == 1


def test_serialised_direct_analysis_can_add_group_contact_override():
    analysis = compas.json_loads(compas.json_dumps(make_direct_analysis()))
    builder = ThreeDECAnalysisBuilder.from_analysis(analysis)
    builder.add_group("arch", nodes=[0])
    builder.add_group("abutment", nodes=[1])

    builder.set_contact_properties_between_groups("arch", "abutment")

    assert len(builder.build().contact_property_overrides) == 1


def test_contact_properties_between_exact_blocks_use_internal_identity_slot(tmp_path):
    builder = ThreeDECAnalysisBuilder.from_meshes([tetrahedron(0.0), tetrahedron(1.0), tetrahedron(2.0)])
    builder.set_material(2500, 25e9, 0.2)
    builder.set_contact_properties()
    builder.set_contact_properties_between_blocks(
        0,
        1,
        kn=40e9,
        kt=20e9,
        friction=20,
    )

    analysis = builder.build()
    solver = ThreeDECSolver(version="7.0", workspace=tmp_path)
    workspace = solver.prepare_run(analysis, run_id="block-pair-contact-test")
    geometry = workspace.file("geometry.dat").read_text(encoding="utf-8")
    deck = workspace.file("analysis.dat").read_text(encoding="utf-8")

    assert "block group 'COMPAS_NODE_0' slot 'COMPAS_ID' range region 0" in geometry
    assert "block group 'COMPAS_NODE_1' slot 'COMPAS_ID' range region 1" in geometry
    assert "COMPAS_NODE_2" not in geometry
    selector = "range group-intersection 'COMPAS_ID=COMPAS_NODE_0' 'COMPAS_ID=COMPAS_NODE_1'"
    assert selector in deck
    assert "block contact property stiffness-normal 40000000000" in deck
    assert "block contact material-table add jmodel mohr property" in deck
    assert len(analysis.contact_block_pair_overrides) == 1
