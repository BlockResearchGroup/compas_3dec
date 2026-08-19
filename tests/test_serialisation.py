import compas
from compas.datastructures import Mesh
from compas.geometry import Transformation

from compas_3dec.solver import ThreeDECAnalysis
from compas_3dec.solver import ThreeDECEntityMap
from compas_3dec.solver import ThreeDECRawResults
from compas_3dec.postprocessing import create_compas_dem_results


def make_analysis():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=0,
        element_guid="block-0",
        region=0,
        vertices=[(0, [0.0, 0.0, 0.0])],
    )
    mapping.add_block(
        node=1,
        element_guid="block-1",
        region=1,
        vertices=[(0, [1.0, 0.0, 0.0])],
    )
    mapping.add_edge((0, 1))

    triangle = Mesh.from_vertices_and_faces(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        [[0, 1, 2]],
    )
    return ThreeDECAnalysis(
        name="serialisation",
        model_id="model-guid",
        problem_id="problem-guid",
        blocks=[
            {
                "node": 0,
                "element_guid": "block-0",
                "region": 0,
                "geometry": triangle,
            }
        ],
        entity_map=mapping,
    )


def test_analysis_compas_json_roundtrip():
    analysis = make_analysis()

    restored = compas.json_loads(compas.json_dumps(analysis))

    assert isinstance(restored, ThreeDECAnalysis)
    assert restored.model_id == "model-guid"
    assert restored.problem_id == "problem-guid"
    assert restored.entity_map.node_for_region(0) == 0
    assert restored.entity_map.edge_for_regions(1, 0) == (0, 1)
    assert isinstance(restored.blocks[0]["geometry"], Mesh)


def test_raw_results_compas_json_roundtrip():
    raw = ThreeDECRawResults(
        blocks=[{"region": 0, "velocity": [1.0, 0.0, 0.0]}],
        metadata={"converged": True},
    )

    restored = compas.json_loads(compas.json_dumps(raw))

    assert isinstance(restored, ThreeDECRawResults)
    assert restored.blocks[0]["region"] == 0
    assert restored.metadata["converged"] is True


def test_create_compas_dem_results_uses_original_graph_keys():
    analysis = make_analysis()
    raw = ThreeDECRawResults(
        blocks=[
            {
                "region": 0,
                "block_id": 100,
                "transformation": Transformation(),
                "velocity": [0.0, 0.0, 0.0],
            }
        ],
        contacts=[
            {
                "contact_id": 500,
                "region_a": 1,
                "region_b": 0,
                "contact_type": "face",
                "point": [0.5, 0.0, 0.0],
                "resultant_global": [3.0, 4.0, 0.0],
            }
        ],
        metadata={"converged": True},
    )

    results = create_compas_dem_results(analysis, raw)

    assert list(results.nodes()) == [0]
    assert results.node_attribute(0, "three_dec_region") == 0
    assert results.node_attribute(0, "three_dec_block_id") == 100
    assert results.face_contact((0, 1)) is True
    assert results.resultant_global((0, 1)) == [3.0, 4.0, 0.0]
    assert results.force_magnitude((0, 1)) == 5.0
    assert results.metadata["converged"] is True


def test_raw_results_offer_explicit_compas_dem_conversion():
    analysis = make_analysis()
    raw = ThreeDECRawResults(
        blocks=[
            {
                "region": 0,
                "block_id": 100,
                "transformation": Transformation(),
            }
        ]
    )

    results = raw.to_compas_dem_results(analysis)

    assert results.model_id == analysis.model_id
    assert results.problem_id == analysis.problem_id
    assert results.node_attribute(0, "three_dec_block_id") == 100


def test_3dec_contacts_create_result_edges_without_input_contact_detection():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=7,
        element_guid="block-7",
        region=70,
        vertices=[],
    )
    mapping.add_block(
        node=42,
        element_guid="block-42",
        region=420,
        vertices=[],
    )
    analysis = ThreeDECAnalysis(
        model_id="model-guid",
        problem_id="problem-guid",
        entity_map=mapping,
    )
    raw = ThreeDECRawResults(
        contacts=[
            {
                "contact_id": 500,
                "region_a": 420,
                "region_b": 70,
                "contact_type": "face-edge",
                "point": [0.5, 0.0, 0.0],
                "resultant_global": [3.0, 0.0, 0.0],
            },
            {
                "contact_id": 501,
                "region_a": 70,
                "region_b": 420,
                "contact_type": "face-edge",
                "point": [0.6, 0.0, 0.0],
                "resultant_global": [2.0, 0.0, 0.0],
            },
        ]
    )

    results = create_compas_dem_results(analysis, raw)

    assert list(results.edges()) == [(42, 7)]
    assert results.edge_contact((7, 42)) is True
    assert results.resultant_global((7, 42)) == [5.0, 0.0, 0.0]
    assert results.edge_attribute((7, 42), "three_dec_contact_types") == ["face-edge"]
    assert analysis.entity_map.edge_for_regions(70, 420) == (42, 7)
    assert analysis.entity_map.edges[0]["contact_ids"] == [500, 501]
    assert analysis.entity_map.edges[0]["source"] == "3dec"
    assert results.metadata["contact_topology_source"] == "3DEC"
