import pytest
from compas.geometry import Transformation

from compas_3dec.solver import ThreeDECAnalysis
from compas_3dec.solver import ThreeDECEntityMap
from compas_3dec.solver import ThreeDECRawResults
from compas_3dec.solver import bind_initial_gridpoints
from compas_3dec.postprocessing import create_compas_dem_results
from compas_3dec.solver import parse_results_text


LOG = """
ordinary 3DEC log output
COMPAS3DEC|META|schema|1
COMPAS3DEC|META|fish_version|9
COMPAS3DEC|META|ratio_local|1.0e-6
COMPAS3DEC|META|timestep|0.01
COMPAS3DEC|BLOCK|100|0|0.5|0.5|0.5|10|1|0|0|0|1|2|3|4|5|6|7|8|9
COMPAS3DEC|GRIDPOINT|1000|0|0|0|0
COMPAS3DEC|CONTACT|500|0|1|face|0.5|0|0|1|0|0
COMPAS3DEC|SUBCONTACT|600|500|0.5|0|0|10|1|2|3|0.01|0.1|0.2|0.3|5|0.5|0.6|0.7|0.25
"""


def test_parse_tagged_fish_output():
    raw = parse_results_text(LOG)

    assert raw.metadata["fish_version"] == 9
    assert raw.metadata["ratio_local"] == pytest.approx(1e-6)
    assert raw.blocks[0]["region"] == 0
    assert raw.gridpoints[0]["gridpoint"] == 1000
    assert raw.contacts[0]["contact_id"] == 500
    assert raw.contacts[0]["resultant_global"] == [11.0, 2.0, 3.0]


def test_parse_schema_2_scalar_shear_stress():
    raw = parse_results_text(
        "\n".join(
            [
                "COMPAS3DEC|META|schema|2",
                "COMPAS3DEC|CONTACT|500|0|1|1|0.5|0|0|1|0|0",
                "COMPAS3DEC|SUBCONTACT|600|500|0.5|0|0|10|1|2|3|0.01|0.1|0.2|0.3|5|0.6|0.25",
            ]
        )
    )

    subcontact = raw.contacts[0]["subcontacts"][0]
    assert subcontact["stress_shear"] == pytest.approx(0.6)
    assert subcontact["area"] == pytest.approx(0.25)


def test_parse_schema_3_subcontact_state():
    raw = parse_results_text(
        "\n".join(
            [
                "COMPAS3DEC|META|schema|3",
                "COMPAS3DEC|CONTACT|500|0|1|1|0.5|0|0|1|0|0",
                "COMPAS3DEC|SUBCONTACT|600|500|0.5|0|0|10|1|2|3|0.01|0.1|0.2|0.3|5|0.6|0.25|5",
            ]
        )
    )

    subcontact = raw.contacts[0]["subcontacts"][0]
    assert subcontact["state"] == 5
    assert subcontact["stress_shear"] == pytest.approx(0.6)
    assert subcontact["area"] == pytest.approx(0.25)


def test_parser_rejects_text_without_tagged_records():
    with pytest.raises(ValueError, match="no COMPAS3DEC"):
        parse_results_text("normal log output only")


def test_parser_reports_malformed_prefix_record_with_line_context():
    with pytest.raises(ValueError, match="Invalid unknown record on log line 1"):
        parse_results_text("COMPAS3DEC|")


def test_parser_normalizes_numeric_3dec_contact_type():
    raw = parse_results_text("COMPAS3DEC|CONTACT|500|0|1|2|0.5|0|0|1|0|0")

    assert raw.contacts[0]["contact_type_code"] == 2
    assert raw.contacts[0]["contact_type"] == "face-edge"


def test_gridpoint_ids_drive_rigid_result_transformation():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=4,
        element_guid="block-4",
        region=4,
        vertices=[
            (0, [0.0, 0.0, 0.0]),
            (1, [1.0, 0.0, 0.0]),
            (2, [0.0, 1.0, 0.0]),
            (3, [0.0, 0.0, 1.0]),
        ],
    )
    analysis = ThreeDECAnalysis(
        model_id="model",
        problem_id="problem",
        entity_map=mapping,
    )
    initial = ThreeDECRawResults(
        gridpoints=[
            {"gridpoint": 10, "region": 4, "xyz": [0.0, 0.0, 0.0]},
            {"gridpoint": 11, "region": 4, "xyz": [1.0, 0.0, 0.0]},
            {"gridpoint": 12, "region": 4, "xyz": [0.0, 1.0, 0.0]},
            {"gridpoint": 13, "region": 4, "xyz": [0.0, 0.0, 1.0]},
        ]
    )
    bind_initial_gridpoints(analysis, initial)

    final = ThreeDECRawResults(
        blocks=[{"block_id": 100, "region": 4}],
        gridpoints=[
            {"gridpoint": 10, "region": 4, "xyz": [2.0, 3.0, 4.0]},
            {"gridpoint": 11, "region": 4, "xyz": [3.0, 3.0, 4.0]},
            {"gridpoint": 12, "region": 4, "xyz": [2.0, 4.0, 4.0]},
            {"gridpoint": 13, "region": 4, "xyz": [2.0, 3.0, 5.0]},
        ],
    )
    results = create_compas_dem_results(analysis, final)

    transformation = results.transformation(4)
    assert isinstance(transformation, Transformation)
    assert results.displacement(4) == pytest.approx([2.0, 3.0, 4.0])


def test_gridpoint_ids_drive_rigid_rotation():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=4,
        element_guid="block-4",
        region=4,
        vertices=[
            (0, [0.0, 0.0, 0.0]),
            (1, [1.0, 0.0, 0.0]),
            (2, [0.0, 1.0, 0.0]),
            (3, [0.0, 0.0, 1.0]),
        ],
    )
    analysis = ThreeDECAnalysis(
        model_id="model",
        problem_id="problem",
        entity_map=mapping,
    )
    initial = ThreeDECRawResults(
        gridpoints=[
            {"gridpoint": 10, "region": 4, "xyz": [0.0, 0.0, 0.0]},
            {"gridpoint": 11, "region": 4, "xyz": [1.0, 0.0, 0.0]},
            {"gridpoint": 12, "region": 4, "xyz": [0.0, 1.0, 0.0]},
            {"gridpoint": 13, "region": 4, "xyz": [0.0, 0.0, 1.0]},
        ]
    )
    bind_initial_gridpoints(analysis, initial)

    final = ThreeDECRawResults(
        blocks=[{"block_id": 100, "region": 4}],
        gridpoints=[
            {"gridpoint": 10, "region": 4, "xyz": [2.0, 3.0, 4.0]},
            {"gridpoint": 11, "region": 4, "xyz": [2.0, 4.0, 4.0]},
            {"gridpoint": 12, "region": 4, "xyz": [1.0, 3.0, 4.0]},
            {"gridpoint": 13, "region": 4, "xyz": [2.0, 3.0, 5.0]},
        ],
    )
    results = create_compas_dem_results(analysis, final)

    matrix = results.transformation(4).matrix
    expected = [
        [0.0, -1.0, 0.0, 2.0],
        [1.0, 0.0, 0.0, 3.0],
        [0.0, 0.0, 1.0, 4.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    for actual_row, expected_row in zip(matrix, expected):
        assert actual_row == pytest.approx(expected_row, abs=1e-8)
