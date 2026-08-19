import pytest

from compas_3dec.solver import ThreeDECEntityMap


def test_block_identity_does_not_depend_on_geometry():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=7,
        element_guid="element-guid",
        region=7,
        vertices=[(0, [0.0, 0.0, 0.0])],
    )

    assert mapping.node_for_region(7) == 7
    assert mapping.region_for_node(7) == 7
    assert mapping.element_guid_for_node(7) == "element-guid"
    assert mapping.node_for_element_guid("element-guid") == 7


def test_gridpoint_binding_uses_coordinates_only_for_initial_match():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=0,
        element_guid="block-0",
        region=0,
        vertices=[
            (10, [0.0, 0.0, 0.0]),
            (11, [1.0, 0.0, 0.0]),
        ],
    )

    bound = mapping.bind_gridpoints(
        node=0,
        gridpoints={
            1001: [1.0, 0.0, 0.0],
            1000: [0.0, 0.0, 0.0],
        },
    )

    assert bound == {10: 1000, 11: 1001}
    assert mapping.gridpoint_for_vertex(0, 10) == 1000
    assert mapping.vertex_for_gridpoint(0, 1001) == 11


def test_gridpoint_binding_rejects_missing_match():
    mapping = ThreeDECEntityMap()
    mapping.add_block(
        node=0,
        element_guid="block-0",
        region=0,
        vertices=[(0, [0.0, 0.0, 0.0])],
    )

    with pytest.raises(ValueError, match="No 3DEC gridpoint"):
        mapping.bind_gridpoints(
            node=0,
            gridpoints={1000: [1.0, 0.0, 0.0]},
            tolerance=1e-6,
        )


def test_edge_lookup_is_orientation_independent():
    mapping = ThreeDECEntityMap()
    mapping.add_block(2, "a", 2, [])
    mapping.add_block(5, "b", 5, [])
    mapping.add_edge((2, 5))

    assert mapping.edge_for_regions(2, 5) == (2, 5)
    assert mapping.edge_for_regions(5, 2) == (2, 5)


def test_contact_output_can_create_a_missing_graph_edge():
    mapping = ThreeDECEntityMap()
    mapping.add_block(2, "a", 20, [])
    mapping.add_block(5, "b", 50, [])

    edge = mapping.bind_contact(50, 20, 9001)
    mapping.bind_contact(20, 50, 9002)

    assert edge == (5, 2)
    assert mapping.edge_for_regions(20, 50) == (5, 2)
    assert mapping.edges == [
        {
            "edge": [5, 2],
            "element_guids": ["b", "a"],
            "regions": [50, 20],
            "contact_ids": [9001, 9002],
            "source": "3dec",
        }
    ]
