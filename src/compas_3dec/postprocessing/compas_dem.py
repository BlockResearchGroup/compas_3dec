from math import atan2
from math import cos
from math import sin
from math import sqrt

from compas.geometry import dot_vectors
from compas.geometry import length_vector
from compas.geometry import sum_vectors


def _sum_vectors(vectors):
    vectors = list(vectors)
    if not vectors:
        return None
    return sum_vectors(vectors)


def _merge_contact_point_forces(points, forces, tolerance=1e-9):
    """Merge coincident contact points and sum their local force components."""
    merged_points = []
    merged_forces = []
    for point, force in zip(points, forces):
        match = next(
            (index for index, existing in enumerate(merged_points) if length_vector([float(point[i]) - float(existing[i]) for i in range(3)]) <= tolerance),
            None,
        )
        if match is None:
            merged_points.append(list(point))
            merged_forces.append(dict(force))
            continue
        for component in ("c_np", "c_nn", "c_u", "c_v"):
            merged_forces[match][component] += float(force[component])
    return merged_points, merged_forces


def _forces_on_polygon_vertices(points, forces, vertices, tolerance=1e-9):
    """Distribute point forces to polygon vertices preserving force and moment."""
    components = ("c_np", "c_nn", "c_u", "c_v")
    distributed = [{key: 0.0 for key in components} for _ in vertices]
    if len(vertices) < 3:
        return list(forces)

    origin = list(vertices[0])
    for point, force in zip(points, forces):
        point_vector = [float(point[i]) - origin[i] for i in range(3)]
        weights = None
        indices = None
        affine_fallback = None
        for index in range(1, len(vertices) - 1):
            a = [float(vertices[index][i]) - origin[i] for i in range(3)]
            b = [float(vertices[index + 1][i]) - origin[i] for i in range(3)]
            aa, ab, bb = dot_vectors(a, a), dot_vectors(a, b), dot_vectors(b, b)
            denominator = aa * bb - ab * ab
            if abs(denominator) <= 1e-30:
                continue
            ap, bp = dot_vectors(a, point_vector), dot_vectors(b, point_vector)
            weight_a = (bb * ap - ab * bp) / denominator
            weight_b = (aa * bp - ab * ap) / denominator
            candidate = [1.0 - weight_a - weight_b, weight_a, weight_b]
            if affine_fallback is None:
                affine_fallback = (candidate, [0, index, index + 1])
            if min(candidate) >= -tolerance and max(candidate) <= 1.0 + tolerance:
                weights = candidate
                indices = [0, index, index + 1]
                break
        if weights is None:
            if affine_fallback is not None:
                # Negative affine weights are intentional when the canonical
                # 3DEC resultant lies outside the contact polygon. They let
                # the COMPAS DEM contact representation preserve both the
                # native force and its moment/application point.
                weights, indices = affine_fallback
            else:
                nearest = min(
                    range(len(vertices)),
                    key=lambda index: length_vector([float(point[i]) - float(vertices[index][i]) for i in range(3)]),
                )
                weights, indices = [1.0], [nearest]
        for vertex_index, weight in zip(indices, weights):
            for component in components:
                distributed[vertex_index][component] += float(force[component]) * weight
    return distributed


def _largest_eigenvector_symmetric(matrix, tolerance=1e-14, max_iterations=64):
    """Return the largest-eigenvalue vector of a small symmetric matrix."""
    size = len(matrix)
    values = [list(row) for row in matrix]
    vectors = [[1.0 if row == column else 0.0 for column in range(size)] for row in range(size)]

    for _ in range(max_iterations):
        p, q = max(
            ((row, column) for row in range(size) for column in range(row + 1, size)),
            key=lambda pair: abs(values[pair[0]][pair[1]]),
        )
        if abs(values[p][q]) <= tolerance:
            break

        angle = 0.5 * atan2(
            2.0 * values[p][q],
            values[q][q] - values[p][p],
        )
        cosine = cos(angle)
        sine = sin(angle)
        app = values[p][p]
        aqq = values[q][q]
        apq = values[p][q]

        for index in range(size):
            if index in (p, q):
                continue
            aip = values[index][p]
            aiq = values[index][q]
            values[index][p] = values[p][index] = cosine * aip - sine * aiq
            values[index][q] = values[q][index] = sine * aip + cosine * aiq

        values[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq
        values[q][q] = sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq
        values[p][q] = values[q][p] = 0.0

        for index in range(size):
            vip = vectors[index][p]
            viq = vectors[index][q]
            vectors[index][p] = cosine * vip - sine * viq
            vectors[index][q] = sine * vip + cosine * viq

    largest = max(range(size), key=lambda index: values[index][index])
    vector = [vectors[row][largest] for row in range(size)]
    length = sqrt(sum(value * value for value in vector))
    return [value / length for value in vector]


def _bestfit_rigid_matrix(source, target):
    """Return a rigid 4x4 transform using Horn's quaternion method."""
    count = len(source)
    source_mean = [sum(point[index] for point in source) / count for index in range(3)]
    target_mean = [sum(point[index] for point in target) / count for index in range(3)]
    matrix = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]

    if count >= 3:
        covariance = [[0.0] * 3 for _ in range(3)]
        for source_point, target_point in zip(source, target):
            a = [source_point[index] - source_mean[index] for index in range(3)]
            b = [target_point[index] - target_mean[index] for index in range(3)]
            for row in range(3):
                for column in range(3):
                    covariance[row][column] += a[row] * b[column]

        sxx, sxy, sxz = covariance[0]
        syx, syy, syz = covariance[1]
        szx, szy, szz = covariance[2]
        horn = [
            [sxx + syy + szz, syz - szy, szx - sxz, sxy - syx],
            [syz - szy, sxx - syy - szz, sxy + syx, szx + sxz],
            [szx - sxz, sxy + syx, -sxx + syy - szz, syz + szy],
            [sxy - syx, szx + sxz, syz + szy, -sxx - syy + szz],
        ]
        w, x, y, z = _largest_eigenvector_symmetric(horn)
        matrix[0][:3] = [
            1.0 - 2.0 * (y * y + z * z),
            2.0 * (x * y - z * w),
            2.0 * (x * z + y * w),
        ]
        matrix[1][:3] = [
            2.0 * (x * y + z * w),
            1.0 - 2.0 * (x * x + z * z),
            2.0 * (y * z - x * w),
        ]
        matrix[2][:3] = [
            2.0 * (x * z - y * w),
            2.0 * (y * z + x * w),
            1.0 - 2.0 * (x * x + y * y),
        ]

    rotated_mean = [sum(matrix[row][column] * source_mean[column] for column in range(3)) for row in range(3)]
    for index in range(3):
        matrix[index][3] = target_mean[index] - rotated_mean[index]
    return matrix


def block_transformation(analysis, raw_results, region):
    """Compute a rigid transformation from persisted gridpoint identities."""
    from compas.geometry import Transformation

    node = analysis.entity_map.node_for_region(region)
    current = {int(record["gridpoint"]): record["xyz"] for record in raw_results.gridpoints if int(record["region"]) == int(region)}
    source = []
    target = []
    for record in analysis.entity_map.vertices:
        if record["node"] != node or record.get("gridpoint") is None:
            continue
        gridpoint = int(record["gridpoint"])
        if gridpoint not in current:
            continue
        source.append(record["xyz"])
        target.append(current[gridpoint])

    if not source:
        return None

    return Transformation.from_matrix(_bestfit_rigid_matrix(source, target))


def create_compas_dem_results(analysis, raw_results, include_native=False):
    """Map parsed 3DEC records to :class:`compas_dem.problem.Results`.

    ``compas_dem`` is imported lazily so that direct command-generation
    parts of ``compas_3dec`` do not require it at import time. By default the
    result contains only the compact interoperability contract. Set
    ``include_native=True`` to duplicate native contact and mechanics records
    into the DEM result for diagnostics; the raw run files are always retained.
    """
    try:
        from compas_dem.interactions import EdgeContact
        from compas_dem.interactions import FrictionContact
        from compas_dem.interactions import VertexContact
        from compas_dem.problem import Results
    except ImportError:
        raise ImportError("compas_dem is required to create compas_dem.Results. Install compas_dem or consume ThreeDECRawResults directly.")

    from compas.geometry import Frame
    from compas.geometry import Plane
    from compas.geometry import Point
    from compas.geometry import Polygon

    mechanics = raw_results.postprocess(
        analysis,
        # Block transformations are populated once below. Requesting blocks
        # here calculated every transformation a first time and discarded it.
        components=("contacts",),
    )
    mechanics_by_id = {record["contact_id"]: record for record in mechanics.contacts}

    results = Results(
        model_id=analysis.model_id,
        problem_id=analysis.problem_id,
    )

    for record in raw_results.blocks:
        region = int(record["region"])
        node = analysis.entity_map.node_for_region(region)
        for attribute, value in record.items():
            if attribute in ("region", "block_id"):
                continue
            results.set_node(node, attribute, value)
        if record.get("transformation") is None:
            transformation = block_transformation(analysis, raw_results, region)
            if transformation is not None:
                results.set_node(node, "transformation", transformation)
        results.set_node(node, "three_dec_region", region)
        if record.get("block_id") is not None:
            results.set_node(node, "three_dec_block_id", int(record["block_id"]))

    contacts_by_edge = {}
    for source_record in raw_results.contacts:
        record = dict(source_record)
        derived = mechanics_by_id.get(int(record["contact_id"]))
        if derived is not None:
            normal_length = length_vector(derived["normal"])
            frame = Frame.from_plane(Plane(derived["origin"], derived["normal"])) if normal_length > 1e-30 else None
            resultant = derived["resultant_force"]
            subcontact_shear = [subcontact["force_shear"] for subcontact in derived["subcontacts"]]
            contact_points = [subcontact["point"] for subcontact in derived["subcontacts"]]
            contact_forces = []
            for subcontact, shear in zip(derived["subcontacts"], subcontact_shear):
                normal_force = float(subcontact["force_normal"])
                contact_forces.append(
                    {
                        "c_np": max(normal_force, 0.0),
                        "c_nn": max(-normal_force, 0.0),
                        "c_u": sum(shear[index] * frame.xaxis[index] for index in range(3)) if frame is not None else 0.0,
                        "c_v": sum(shear[index] * frame.yaxis[index] for index in range(3)) if frame is not None else 0.0,
                    }
                )
            contact_data = None
            interaction_points, interaction_forces = _merge_contact_point_forces(
                contact_points,
                contact_forces,
            )
            if frame is not None and len(interaction_points) >= 3:
                contact_data = FrictionContact(
                    points=interaction_points,
                )
                contact_data._frame = frame
                summary_force = {component: sum(float(force[component]) for force in contact_forces) for component in ("c_np", "c_nn", "c_u", "c_v")}
                contact_data.forces = _forces_on_polygon_vertices(
                    [derived["resultant_point"]],
                    [summary_force],
                    contact_data.points,
                )
            elif frame is not None and len(interaction_points) == 2:
                contact_data = EdgeContact(
                    points=interaction_points,
                    frame=frame,
                    forces=interaction_forces,
                )
            elif frame is not None and len(interaction_points) == 1:
                contact_data = VertexContact(
                    point=Point(*interaction_points[0]),
                    frame=frame,
                    forces=interaction_forces,
                )
            converted = {
                "contact_geometry": derived["geometry"],
                "contact_polygon": derived["geometry"] if isinstance(derived["geometry"], Polygon) else None,
                "contact_frame": frame,
                "contact_frames": [frame] * len(derived["subcontacts"]) if frame is not None else None,
                "contact_points": contact_points,
                "contact_data": contact_data,
                "resultant_global": resultant,
                "resultant_local": [sum(resultant[index] * axis[index] for index in range(3)) for axis in (frame.xaxis, frame.yaxis, frame.zaxis)] if frame is not None else None,
                "force_point": derived["resultant_point"],
                "force_normal": [subcontact["force_normal"] for subcontact in derived["subcontacts"]],
                "force_tangent1": [sum(force[index] * frame.xaxis[index] for index in range(3)) for force in subcontact_shear] if frame is not None else None,
                "force_tangent2": [sum(force[index] * frame.yaxis[index] for index in range(3)) for force in subcontact_shear] if frame is not None else None,
                "force_vector": [
                    _sum_vectors(
                        [
                            subcontact["force_normal_vector"],
                            subcontact["force_shear"],
                        ]
                    )
                    for subcontact in derived["subcontacts"]
                ],
                "nodal_force_magnitudes": [
                    length_vector(
                        _sum_vectors(
                            [
                                subcontact["force_normal_vector"],
                                subcontact["force_shear"],
                            ]
                        )
                    )
                    for subcontact in derived["subcontacts"]
                ],
                "gap": [subcontact["displacement_normal"] for subcontact in derived["subcontacts"]],
                "status": ["open" if subcontact["open"] else "sliding" if subcontact["sliding"] else "closed" for subcontact in derived["subcontacts"]],
            }
            # The derived dictionary duplicates the native contact mechanics
            # and can be large. Keep it only for the explicit diagnostic route.
            if include_native:
                converted["three_dec_mechanics"] = derived
            record.update(converted)
        edge = analysis.entity_map.bind_contact(
            record["region_a"],
            record["region_b"],
            record["contact_id"],
        )
        contacts_by_edge.setdefault(edge, []).append(record)

    standard_contact_attributes = (
        "contact_polygon",
        "contact_geometry",
        "contact_frame",
        "contact_frames",
        "contact_data",
        "resultant_local",
        "force_point",
        "status",
        "gap",
        "contact_points",
        "force_normal",
        "force_tangent1",
        "force_tangent2",
        "force_vector",
        "nodal_force_magnitudes",
    )

    for edge, records in contacts_by_edge.items():
        if include_native:
            results.set_edge(edge, "three_dec_contacts", records)

        points = [record["point"] for record in records if record.get("point") is not None]
        if points:
            results.set_edge(edge, "contact_points", points)

        global_resultant = _sum_vectors(record["resultant_global"] for record in records if record.get("resultant_global") is not None)
        if global_resultant is not None:
            results.set_edge(edge, "resultant_global", global_resultant)
            results.set_edge(
                edge,
                "force_magnitude",
                length_vector(global_resultant),
            )

        contact_types = {str(record.get("contact_type", "")).lower().replace("_", "-") for record in records}
        results.set_edge(
            edge,
            "three_dec_contact_types",
            sorted(contact_types),
        )
        results.set_edge(
            edge,
            "face_contact",
            bool(contact_types.intersection(["face", "face-face"])),
        )
        results.set_edge(
            edge,
            "edge_contact",
            bool(contact_types.intersection(["edge", "face-edge", "edge-face"])),
        )
        results.set_edge(
            edge,
            "point_contact",
            bool(
                contact_types.intersection(
                    [
                        "face-vertex",
                        "vertex-face",
                        "edge-edge",
                        "edge-vertex",
                        "vertex-edge",
                        "vertex-vertex",
                        "point",
                        "vertex",
                    ]
                )
            ),
        )

        if len(records) == 1:
            record = records[0]
            for attribute in standard_contact_attributes:
                if record.get(attribute) is not None:
                    results.set_edge(edge, attribute, record[attribute])
            if include_native and record.get("three_dec_mechanics") is not None:
                results.set_edge(edge, "three_dec_mechanics", record["three_dec_mechanics"])

    results.metadata.update(raw_results.metadata)
    results.metadata.update(
        {
            "solver": "3DEC",
            "analysis_id": str(analysis.guid),
            "three_dec_result_schema": raw_results.schema_version,
            "contact_topology_source": "3DEC",
            "contact_edge_count": len(contacts_by_edge),
            "contact_count": len(raw_results.contacts),
        }
    )
    return results
