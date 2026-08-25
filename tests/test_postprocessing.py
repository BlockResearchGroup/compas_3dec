import compas
import pytest
from compas.datastructures import Mesh

from compas_3dec.rhino import draw_results
from compas_3dec.solver import ThreeDECRawResults
from compas_3dec.postprocessing import postprocess_raw_results
from compas_3dec.postprocessing import ThreeDECPostProcessor
from compas_3dec.postprocessing import ThreeDECPostProcessedResults
from compas_3dec.rhino import build_visualisation
from compas_3dec import ThreeDECAnalysisBuilder


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
    builder = ThreeDECAnalysisBuilder.from_meshes([tetrahedron(0.0), tetrahedron(1.0)])
    builder.set_material(density=1800, young_modulus=25e9, poisson_ratio=0.2)
    builder.set_supports([0])
    builder.set_contact_properties(kn=1e9, kt=5e8, friction=35.0)
    builder.add_gravity()
    return builder.build()


def make_raw_contact_results():
    points = [
        [-1.0, -1.0, 0.0],
        [1.0, -1.0, 0.0],
        [1.0, 1.0, 0.0],
        [-1.0, 1.0, 0.0],
    ]
    shear = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [6.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
    subcontacts = []
    for index, (point, shear_force) in enumerate(zip(points, shear), start=1):
        subcontacts.append(
            {
                "subcontact_id": index,
                "point": point,
                "force_normal": 10.0,
                "force_shear": shear_force,
                "displacement_normal": 0.01 if index == 1 else 0.0,
                "displacement_shear": [0.001, 0.0, 0.0] if index == 3 else [0.0, 0.0, 0.0],
                "stress_normal": 10.0,
                "stress_shear": 0.0,
                "area": 1.0,
                "state": 1 if index == 3 else 0,
            }
        )
    return ThreeDECRawResults(
        contacts=[
            {
                "contact_id": 50,
                "region_a": 0,
                "region_b": 1,
                "contact_type": "face-face",
                "point": [0.0, 0.0, 0.0],
                "normal": [0.0, 0.0, 1.0],
                "subcontacts": subcontacts,
            }
        ]
    )


def test_native_postprocessing_derives_resultants_friction_cracks_and_hinge():
    analysis = make_direct_analysis()
    post = postprocess_raw_results(
        analysis,
        make_raw_contact_results(),
        friction_coefficient=0.5,
        opening_tolerance=1e-6,
    )
    post.metadata["result_state"] = "final"

    contact = post.contacts[0]
    assert contact["resultant_normal"] == [0.0, 0.0, 40.0]
    assert contact["resultant_shear"] == [8.0, 0.0, 0.0]
    assert contact["resultant_force"] == [8.0, 0.0, 40.0]
    assert contact["friction_capacity"] == 20.0
    assert contact["friction_utilisation"] == pytest.approx(0.4)
    assert contact["sliding"] is True
    assert contact["subcontacts"][2]["sliding"] is True
    assert contact["subcontacts"][2]["sliding_native"] is True
    assert contact["subcontacts"][2]["sliding_kinematic"] is True
    assert contact["subcontacts"][2]["sliding_confirmed"] is True
    assert contact["subcontacts"][2]["sliding_inconsistent"] is False
    assert contact["subcontacts"][2]["friction_limit_reached"] is True
    assert contact["subcontacts"][2]["shear_displacement_magnitude"] == pytest.approx(0.001)
    assert contact["cracked"] is True
    assert contact["opening_points"] == [[-1.0, -1.0, 0.0]]
    assert contact["hinge_points"] == [[1.0, 1.0, 0.0]]
    assert contact["normal_application_point"] != contact["shear_application_point"]
    assert contact["resultant_point"] == contact["normal_application_point"]
    for key in (
        "resultant_point",
        "normal_application_point",
        "shear_application_point",
    ):
        assert contact[key][2] == pytest.approx(0.0)
    assert any(abs(value) > 0.0 for value in contact["torque_at_normal_point"])

    arm = [contact["resultant_point"][index] - contact["origin"][index] for index in range(3)]
    force = contact["resultant_force"]
    arm_cross_force = [
        arm[1] * force[2] - arm[2] * force[1],
        arm[2] * force[0] - arm[0] * force[2],
        arm[0] * force[1] - arm[1] * force[0],
    ]
    reconstructed_moment = [contact["residual_torque"][index] + arm_cross_force[index] for index in range(3)]
    assert reconstructed_moment == pytest.approx(contact["moment_about_origin"])


def test_selective_postprocessing_skips_unrequested_work():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()

    blocks = raw.postprocess_blocks(analysis)
    contacts = raw.postprocess_contacts(analysis)
    failure = raw.postprocess_failure(
        analysis,
        friction_coefficient=0.5,
    )

    assert blocks.blocks == []  # no raw block records in this fixture
    assert blocks.contacts == []
    assert contacts.blocks == []
    assert "friction_capacity" not in contacts.contacts[0]
    assert "hinge_points" not in contacts.contacts[0]
    assert failure.blocks == []
    assert "friction_capacity" in failure.contacts[0]
    assert "hinge_points" in failure.contacts[0]
    assert contacts.contacts[0]["resultant_force"] == pytest.approx(failure.contacts[0]["resultant_force"])
    assert contacts.contacts[0]["resultant_point"] == pytest.approx(failure.contacts[0]["resultant_point"])


def test_postprocessor_owns_selective_operations():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()
    processor = ThreeDECPostProcessor(analysis, raw)

    contacts = processor.contacts()
    failure = processor.failure(friction_coefficient=0.5)

    assert contacts.metadata["postprocessing_components"] == ["contacts"]
    assert failure.metadata["postprocessing_components"] == [
        "contacts",
        "failure",
    ]


def test_friction_limit_without_shear_displacement_is_not_confirmed_sliding():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()
    raw.contacts[0]["subcontacts"][2]["displacement_shear"] = [0.0, 0.0, 0.0]

    contact = postprocess_raw_results(
        analysis,
        raw,
        friction_coefficient=0.5,
        shear_displacement_tolerance=1e-9,
    ).contacts[0]

    subcontact = contact["subcontacts"][2]
    assert subcontact["friction_limit_reached"] is True
    assert subcontact["sliding"] is False
    assert subcontact["sliding_native"] is True
    assert subcontact["sliding_kinematic"] is False
    assert subcontact["sliding_inconsistent"] is True
    assert contact["friction_limit_reached"] is True
    assert contact["sliding"] is False


def test_native_state_must_agree_before_sliding_is_confirmed():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()
    raw.contacts[0]["subcontacts"][2]["state"] = 4

    contact = raw.postprocess_failure(
        analysis,
        friction_coefficient=0.5,
    ).contacts[0]
    subcontact = contact["subcontacts"][2]

    assert subcontact["sliding_native"] is False
    assert subcontact["sliding_past"] is True
    assert subcontact["friction_limit_reached"] is True
    assert subcontact["sliding_kinematic"] is True
    assert subcontact["sliding_confirmed"] is False
    assert subcontact["sliding_inconsistent"] is True
    assert contact["sliding"] is False
    assert contact["sliding_past"] is True
    assert contact["sliding_inconsistent"] is True


def test_postprocessed_results_are_compas_serializable():
    analysis = make_direct_analysis()
    post = postprocess_raw_results(
        analysis,
        make_raw_contact_results(),
        friction_coefficient=0.5,
    )

    restored = compas.json_loads(compas.json_dumps(post))

    assert isinstance(restored, ThreeDECPostProcessedResults)
    assert restored.contacts[0]["contact_id"] == 50
    assert restored.contacts[0]["geometry"] is not None


def test_compas_dem_conversion_is_compact_by_default_and_native_is_opt_in():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()

    results = raw.to_compas_dem_results(analysis)
    edge = (0, 1)

    assert results.contact_geometry(edge) is not None
    assert results.contact_frame(edge) is not None
    assert results.contact_data(edge) is not None
    assert len(results.contact_frames(edge)) == 4
    assert results.force_point(edge) is not None
    assert results.force_normal(edge) == [10.0] * 4
    assert len(results.force_tangent1(edge)) == 4
    assert len(results.force_tangent2(edge)) == 4
    assert results.status(edge)[0] == "open"
    assert results.edge_attribute(edge, "three_dec_mechanics") is None
    assert results.edge_attribute(edge, "three_dec_contacts") is None
    dem_contact = results.contact_data(edge)
    native = raw.postprocess(analysis).contacts[0]
    assert list(dem_contact.resultantline().vector) == pytest.approx(native["resultant_force"])
    assert list(dem_contact.resultantpoint) == pytest.approx(native["resultant_point"])

    diagnostic = raw.to_compas_dem_results(analysis, include_native=True)
    assert diagnostic.edge_attribute(edge, "three_dec_mechanics") is not None
    assert diagnostic.edge_attribute(edge, "three_dec_contacts") is not None


def test_compas_dem_adapter_preserves_exterior_native_resultant_point():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()
    for subcontact, normal_force in zip(
        raw.contacts[0]["subcontacts"],
        [10.0, 10.0, -5.0, -5.0],
    ):
        subcontact["force_normal"] = normal_force

    native = raw.postprocess_contacts(analysis).contacts[0]
    dem = raw.to_compas_dem_results(analysis)
    dem_contact = dem.contact_data((0, 1))

    assert native["resultant_point"][1] < -1.0
    assert list(dem_contact.resultantline().vector) == pytest.approx(native["resultant_force"])
    assert list(dem_contact.resultantpoint) == pytest.approx(native["resultant_point"])
    assert dem.resultant_global((0, 1)) == pytest.approx(native["resultant_force"])
    assert dem.force_point((0, 1)) == pytest.approx(native["resultant_point"])


def test_rhino_visualisation_contains_requested_mechanics():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()
    post = postprocess_raw_results(
        analysis,
        raw,
        friction_coefficient=0.5,
        opening_tolerance=1e-6,
    )

    visual = build_visualisation(
        analysis,
        post,
        gravity_postprocessed=post,
        force_scale=0.01,
        displacement_scale=10.0,
        reaction_force_factor=1.0,
        reaction_force_unit="N",
    )

    assert len(visual["initial_blocks"]) == 2
    assert len(visual["gravity_blocks"]) == 1
    assert len(visual["gravity_support_blocks"]) == 1
    assert len(visual["updated_blocks"]) == 1
    assert len(visual["updated_support_blocks"]) == 1
    assert len(visual["contact_geometry"]) == 1
    assert len(visual["normal_force_lines"]) == 8
    assert len(visual["shear_force_lines"]) == 4
    assert len(visual["resultant_force_lines"]) == 2
    assert len(visual["resultant_normal_lines"]) == 2
    assert len(visual["resultant_shear_lines"]) == 2
    assert len(visual["transported_shear_lines"]) == 2
    application_point = visual["resultant_points"][0]
    for category in (
        "resultant_force_lines",
        "resultant_normal_lines",
        "transported_shear_lines",
    ):
        assert all(line.start == application_point for line in visual[category])
    shear_point = visual["shear_application_points"][0]
    assert all(line.start == shear_point for line in visual["resultant_shear_lines"])
    assert len(visual["torque_lines"]) == 2
    assert len(visual["shear_lines_of_action"]) == 1
    assert len(visual["friction_sliding_points"]) == 1
    assert len(visual["crack_points"]) == 1
    assert len(visual["hinge_points"]) == 1
    assert len(visual["reaction_force_lines"]) == 3
    assert len(visual["reaction_points"]) == 1
    assert visual["reaction_points"][0] == application_point
    assert visual["reaction_labels"][0]["text"].endswith(" N")
    assert visual["reaction_magnitude_labels"][0]["text"].endswith(" N")
    assert visual["reaction_component_labels"][0]["text"].startswith("Fx=")
    reaction = visual["reaction_force_lines"][0].vector
    toward_support = [-1.0, 0.0, 0.0]
    assert sum(reaction[index] * toward_support[index] for index in range(3)) > 0.0


def test_reaction_component_labels_are_optional():
    analysis = make_direct_analysis()
    post = postprocess_raw_results(analysis, make_raw_contact_results())

    components = build_visualisation(
        analysis,
        post,
        force_scale=0.01,
        reaction_label_mode="components",
        reaction_force_factor=1.0,
        reaction_force_unit="N",
        reaction_label_decimals=2,
    )
    hidden = build_visualisation(
        analysis,
        post,
        force_scale=0.01,
        reaction_label_mode=None,
    )

    assert components["reaction_labels"][0]["text"].startswith("Fx=")
    assert hidden["reaction_labels"] == []


def test_automatic_resultant_and_reaction_scale_fits_block_size():
    analysis = make_direct_analysis()
    post = postprocess_raw_results(analysis, make_raw_contact_results())

    visual = build_visualisation(
        analysis,
        post,
        force_length_ratio=0.5,
    )

    block_diagonal = 3.0**0.5
    maximum_length = 0.5 * block_diagonal
    assert visual["resultant_force_lines"][0].length <= maximum_length + 1e-12
    assert visual["reaction_force_lines"][0].length == pytest.approx(visual["resultant_force_lines"][0].length)


def test_rhino_visualiser_requires_rhino_runtime():
    analysis = make_direct_analysis()
    raw = make_raw_contact_results()
    postprocessed = postprocess_raw_results(
        analysis,
        raw,
        friction_coefficient=0.5,
    )

    with pytest.raises(RuntimeError, match="inside Rhino"):
        draw_results(
            analysis,
            raw,
            postprocessed=postprocessed,
        )
