from math import sqrt

from compas.data import Data


class ThreeDECEntityMap(Data):
    """Persistent correspondence between analysis and 3DEC entities.

    Block identity is explicit and does not depend on geometry. Coordinates are
    retained only to establish the initial mesh-vertex to 3DEC-gridpoint
    correspondence. Once bound, result import uses the gridpoint IDs.

    Parameters
    ----------
    blocks : list[dict], optional
        Block identity records.
    vertices : list[dict], optional
        Mesh vertex and 3DEC gridpoint records.
    edges : list[dict], optional
        Interaction graph edge and 3DEC contact records.
    schema_version : int, optional
        Version of the serialised mapping schema.
    name : str, optional
        Name of the mapping.
    """

    CURRENT_SCHEMA_VERSION = 2

    def __init__(
        self,
        blocks=None,
        vertices=None,
        edges=None,
        schema_version=None,
        name=None,
    ):
        super().__init__(name=name)
        self.schema_version = schema_version or self.CURRENT_SCHEMA_VERSION
        self.blocks = list(blocks or [])
        self.vertices = list(vertices or [])
        self.edges = list(edges or [])
        self._rebuild_indices()

    @property
    def __data__(self):
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "blocks": self.blocks,
            "vertices": self.vertices,
            "edges": self.edges,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            name=data.get("name"),
            schema_version=data.get("schema_version", 1),
            blocks=data.get("blocks", []),
            vertices=data.get("vertices", []),
            edges=data.get("edges", []),
        )

    def _rebuild_indices(self):
        self._block_by_node = {}
        self._block_by_region = {}
        self._block_by_guid = {}
        self._edge_by_regions = {}

        for record in self.blocks:
            node = int(record["node"])
            region = int(record["region"])
            record["node"] = node
            record["region"] = region
            record["element_guid"] = str(record["element_guid"])
            self._block_by_node[node] = record
            self._block_by_region[region] = record
            self._block_by_guid[record["element_guid"]] = record

        for record in self.vertices:
            record["node"] = int(record["node"])
            if record.get("gridpoint") is not None:
                record["gridpoint"] = int(record["gridpoint"])

        for record in self.edges:
            record["edge"] = [int(record["edge"][0]), int(record["edge"][1])]
            record["regions"] = [int(record["regions"][0]), int(record["regions"][1])]
            record["contact_ids"] = [int(value) for value in record.get("contact_ids", [])]
            record["source"] = record.get("source", "model")
            self._edge_by_regions[frozenset(record["regions"])] = record

    def add_block(self, node, element_guid, region, vertices):
        """Register a block and its initial mesh vertices."""
        if not isinstance(node, int):
            raise TypeError("COMPAS DEM graph node identifiers must be integers.")
        if not isinstance(region, int):
            raise TypeError("3DEC region identifiers must be integers.")
        if node in self._block_by_node:
            raise ValueError("Graph node {} is already mapped.".format(node))
        if region in self._block_by_region:
            raise ValueError("3DEC region {} is already mapped.".format(region))

        guid = str(element_guid)
        if guid in self._block_by_guid:
            raise ValueError("Element GUID {} is already mapped.".format(guid))

        record = {
            "node": node,
            "element_guid": guid,
            "region": region,
        }
        self.blocks.append(record)
        self._block_by_node[node] = record
        self._block_by_region[region] = record
        self._block_by_guid[guid] = record

        for vertex, xyz in vertices:
            self.vertices.append(
                {
                    "node": node,
                    "vertex": vertex,
                    "xyz": [float(value) for value in xyz],
                    "gridpoint": None,
                }
            )

    def add_edge(self, edge, contact_ids=None, source="model"):
        """Register an interaction graph edge.

        The edge orientation from the COMPAS model is preserved. Lookup by
        region pair is orientation independent.
        """
        u, v = int(edge[0]), int(edge[1])
        if u not in self._block_by_node or v not in self._block_by_node:
            raise KeyError("Both edge nodes must be registered before the edge.")

        regions = [self.region_for_node(u), self.region_for_node(v)]
        key = frozenset(regions)
        if key in self._edge_by_regions:
            raise ValueError("An edge for 3DEC regions {} is already mapped.".format(regions))

        record = {
            "edge": [u, v],
            "element_guids": [
                self.element_guid_for_node(u),
                self.element_guid_for_node(v),
            ],
            "regions": regions,
            "contact_ids": [int(value) for value in (contact_ids or [])],
            "source": str(source),
        }
        self.edges.append(record)
        self._edge_by_regions[key] = record

    def node_for_region(self, region):
        return self._block_by_region[int(region)]["node"]

    def region_for_node(self, node):
        return self._block_by_node[int(node)]["region"]

    def element_guid_for_node(self, node):
        return self._block_by_node[int(node)]["element_guid"]

    def node_for_element_guid(self, element_guid):
        return self._block_by_guid[str(element_guid)]["node"]

    def edge_for_regions(self, region_a, region_b):
        record = self._edge_by_regions.get(frozenset([int(region_a), int(region_b)]))
        if record is None:
            raise KeyError(
                "No COMPAS DEM edge corresponds to 3DEC regions {} and {}.".format(
                    region_a,
                    region_b,
                )
            )
        return tuple(record["edge"])

    def bind_contact(self, region_a, region_b, contact_id):
        """Associate a 3DEC contact with an edge, creating it when discovered.

        3DEC is authoritative for contact topology. Therefore an input
        ``BlockModel`` does not need to contain contact edges before solving.
        """
        region_a = int(region_a)
        region_b = int(region_b)
        key = frozenset([region_a, region_b])
        record = self._edge_by_regions.get(key)
        if record is None:
            node_a = self.node_for_region(region_a)
            node_b = self.node_for_region(region_b)
            self.add_edge(
                (node_a, node_b),
                source="3dec",
            )
            record = self._edge_by_regions[key]

        contact_id = int(contact_id)
        if contact_id not in record["contact_ids"]:
            record["contact_ids"].append(contact_id)
        return tuple(record["edge"])

    def bind_gridpoints(self, node, gridpoints, tolerance=1e-6, overwrite=False):
        """Bind initial mesh vertices to 3DEC gridpoints by coordinates.

        This is the only geometry-based part of the identity mapping. Every
        match must be unique and within ``tolerance``. The resulting
        gridpoint IDs are then persisted and used for all later result states.

        Parameters
        ----------
        node : int
            COMPAS DEM graph node.
        gridpoints : dict[int, sequence[float]] | list[dict]
            Either ``{gridpoint_id: xyz}`` or records containing ``id`` and
            ``xyz``.
        tolerance : float, optional
            Maximum initial coordinate distance.
        overwrite : bool, optional
            Permit replacement of an existing binding.
        """
        node = int(node)
        if node not in self._block_by_node:
            raise KeyError("Graph node {} is not mapped.".format(node))
        if tolerance <= 0:
            raise ValueError("The gridpoint matching tolerance must be positive.")

        if isinstance(gridpoints, dict):
            candidates = [(int(gridpoint), [float(value) for value in xyz]) for gridpoint, xyz in gridpoints.items()]
        else:
            candidates = [
                (
                    int(record.get("id", record.get("gridpoint"))),
                    [float(value) for value in record["xyz"]],
                )
                for record in gridpoints
            ]

        records = [record for record in self.vertices if record["node"] == node]
        if not records:
            raise ValueError("Graph node {} has no registered mesh vertices.".format(node))

        used = set()
        tolerance_squared = tolerance * tolerance
        ambiguity_epsilon = max(tolerance_squared * 1e-9, 1e-24)

        for record in records:
            if record.get("gridpoint") is not None and not overwrite:
                used.add(int(record["gridpoint"]))
                continue

            distances = []
            for gridpoint, xyz in candidates:
                if gridpoint in used:
                    continue
                distance_squared = sum((float(a) - float(b)) ** 2 for a, b in zip(record["xyz"], xyz))
                if distance_squared <= tolerance_squared:
                    distances.append((distance_squared, gridpoint))

            distances.sort()
            if not distances:
                raise ValueError(
                    "No 3DEC gridpoint is within {} of vertex {} on graph node {}.".format(
                        tolerance,
                        record["vertex"],
                        node,
                    )
                )
            if len(distances) > 1 and abs(distances[1][0] - distances[0][0]) <= ambiguity_epsilon:
                raise ValueError(
                    "Ambiguous 3DEC gridpoint match for vertex {} on graph node {}.".format(
                        record["vertex"],
                        node,
                    )
                )

            record["gridpoint"] = distances[0][1]
            used.add(distances[0][1])

        return {record["vertex"]: record["gridpoint"] for record in records}

    def gridpoint_for_vertex(self, node, vertex):
        node = int(node)
        for record in self.vertices:
            if record["node"] == node and record["vertex"] == vertex:
                if record.get("gridpoint") is None:
                    raise ValueError(
                        "Vertex {} on graph node {} has not been bound to a gridpoint.".format(
                            vertex,
                            node,
                        )
                    )
                return record["gridpoint"]
        raise KeyError("Vertex {} on graph node {} is not mapped.".format(vertex, node))

    def vertex_for_gridpoint(self, node, gridpoint):
        node = int(node)
        gridpoint = int(gridpoint)
        for record in self.vertices:
            if record["node"] == node and record.get("gridpoint") == gridpoint:
                return record["vertex"]
        raise KeyError("Gridpoint {} on graph node {} is not mapped.".format(gridpoint, node))

    def gridpoint_distance(self, node, vertex, xyz):
        """Return the distance from a stored initial vertex position."""
        node = int(node)
        for record in self.vertices:
            if record["node"] == node and record["vertex"] == vertex:
                return sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(record["xyz"], xyz)))
        raise KeyError("Vertex {} on graph node {} is not mapped.".format(vertex, node))
