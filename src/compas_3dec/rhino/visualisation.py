from compas.geometry import Line
from compas.geometry import Point


def _length(vector):
    return sum(float(value) ** 2 for value in vector) ** 0.5


def _dot(a, b):
    return sum(float(a[index]) * float(b[index]) for index in range(3))


def _cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _line(point, vector, scale):
    if _length(vector) <= 1e-30:
        return None
    return Line(point, [point[index] + vector[index] * scale for index in range(3)])


def _action_reaction_lines(point, vector, scale):
    """Return equal and opposite vectors with a shared application point."""
    line = _line(point, vector, scale)
    reaction = _line(point, [-value for value in vector], scale)
    return [candidate for candidate in (line, reaction) if candidate is not None]


def _arrow_lines(point, vector, scale, model_size):
    """Create an arrow shaft and two arrowhead lines."""
    shaft = _line(point, vector, scale)
    if shaft is None:
        return []
    direction = [value / _length(vector) for value in vector]
    reference = [0.0, 0.0, 1.0]
    if abs(_dot(direction, reference)) > 0.9:
        reference = [0.0, 1.0, 0.0]
    side = _cross(direction, reference)
    side_length = _length(side)
    side = [value / side_length for value in side]
    arrow_length = min(0.25 * shaft.length, 0.025 * model_size)
    endpoint = list(shaft.end)
    backward = [endpoint[i] - direction[i] * arrow_length for i in range(3)]
    width = 0.45 * arrow_length
    return [
        shaft,
        Line(endpoint, [backward[i] + side[i] * width for i in range(3)]),
        Line(endpoint, [backward[i] - side[i] * width for i in range(3)]),
    ]


def _model_size(analysis):
    coordinates = []
    for block in analysis.blocks:
        mesh = block["geometry"]
        coordinates.extend(mesh.vertices_attributes("xyz"))
    if not coordinates:
        return 1.0
    minimum = [min(point[index] for point in coordinates) for index in range(3)]
    maximum = [max(point[index] for point in coordinates) for index in range(3)]
    diagonal = _length([maximum[index] - minimum[index] for index in range(3)])
    return diagonal or 1.0


def _block_size(analysis, fallback):
    """Return the smallest block bounding-box diagonal."""
    sizes = []
    for block in analysis.blocks:
        points = block["geometry"].vertices_attributes("xyz")
        if not points:
            continue
        minimum = [min(point[index] for point in points) for index in range(3)]
        maximum = [max(point[index] for point in points) for index in range(3)]
        diagonal = _length([maximum[index] - minimum[index] for index in range(3)])
        if diagonal > 1e-30:
            sizes.append(diagonal)
    return min(sizes or [fallback])


def _interface_size(contact_geometry, fallback):
    """Return the largest distance between vertices of a contact polygon."""
    if contact_geometry is None:
        return fallback
    points = list(contact_geometry.points)
    distances = [_length([a[index] - b[index] for index in range(3)]) for position, a in enumerate(points) for b in points[position + 1 :]]
    return max(distances or [fallback])


def build_visualisation(
    analysis,
    postprocessed,
    gravity_postprocessed=None,
    force_scale=None,
    torque_scale=None,
    displacement_scale=1.0,
    line_of_action_length=None,
    reaction_label_mode="magnitude",
    reaction_force_factor=0.001,
    reaction_force_unit="kN",
    reaction_label_decimals=1,
    force_length_ratio=0.5,
    prescribed_displacement_scale=None,
    displacement_label_decimals=4,
):
    """Build backend-neutral COMPAS geometry for Rhino output."""
    model_size = _model_size(analysis)
    if force_scale is None:
        force_magnitudes = [_length(contact["resultant_force"]) for contact in postprocessed.contacts]
        force_magnitudes.extend(_length(load["force"]) for load in postprocessed.metadata.get("applied_loads", []))
        maximum_force = max(force_magnitudes or [0.0])
        maximum_length = float(force_length_ratio) * _block_size(
            analysis,
            model_size,
        )
        force_scale = maximum_length / maximum_force if maximum_force > 1e-30 else 1.0
    if torque_scale is None:
        torque_magnitudes = [_length(contact["torque_at_normal_point"]) for contact in postprocessed.contacts]
        maximum_torque = max(torque_magnitudes or [0.0])
        torque_scale = 0.10 * model_size / maximum_torque if maximum_torque > 1e-30 else force_scale
    geometry = {
        "initial_blocks": [],
        "gravity_blocks": [],
        "gravity_support_blocks": [],
        "updated_blocks": [],
        "updated_support_blocks": [],
        "contact_geometry": [],
        "subcontact_points": [],
        "normal_force_lines": [],
        "shear_force_lines": [],
        "resultant_force_lines": [],
        "resultant_normal_lines": [],
        "resultant_shear_lines": [],
        "transported_shear_lines": [],
        "torque_lines": [],
        "shear_lines_of_action": [],
        "resultant_points": [],
        "normal_application_points": [],
        "shear_application_points": [],
        "friction_safe_points": [],
        "friction_limit_points": [],
        "friction_sliding_points": [],
        "crack_points": [],
        "hinge_points": [],
        "opening_lines": [],
        "reaction_force_lines": [],
        "reaction_points": [],
        "reaction_labels": [],
        "reaction_magnitude_labels": [],
        "reaction_component_labels": [],
        "applied_load_lines": [],
        "applied_load_points": [],
        "applied_load_labels": [],
        "prescribed_displacement_lines": [],
        "prescribed_displacement_points": [],
        "prescribed_displacement_labels": [],
    }

    block_centroids = {}
    block_transformations = {}
    for block in analysis.blocks:
        geometry["initial_blocks"].append(block["geometry"].copy())

    def add_state_blocks(results, regular_category, support_category, track=False):
        records = {record["node"]: record for record in results.blocks}
        for block in analysis.blocks:
            mesh = block["geometry"].copy()
            record = records.get(block["node"])
            transformation = record.get("transformation") if record else None
            if transformation is not None:
                if displacement_scale != 1.0:
                    matrix = [row[:] for row in transformation.matrix]
                    matrix[0][3] *= displacement_scale
                    matrix[1][3] *= displacement_scale
                    matrix[2][3] *= displacement_scale
                    from compas.geometry import Transformation

                    transformation = Transformation.from_matrix(matrix)
                mesh.transform(transformation)
            category = support_category if block["node"] in analysis.supports else regular_category
            geometry[category].append(mesh)
            if track:
                block_centroids[block["node"]] = list(mesh.centroid())
                if transformation is not None:
                    block_transformations[block["node"]] = transformation

    selected_state = str(postprocessed.metadata.get("result_state") or "updated")
    if gravity_postprocessed is not None:
        add_state_blocks(gravity_postprocessed, "gravity_blocks", "gravity_support_blocks")
    if selected_state == "gravity":
        if gravity_postprocessed is None:
            add_state_blocks(postprocessed, "gravity_blocks", "gravity_support_blocks", track=True)
        else:
            add_state_blocks(postprocessed, "updated_blocks", "updated_support_blocks", track=True)
            geometry["updated_blocks"] = []
            geometry["updated_support_blocks"] = []
    else:
        add_state_blocks(postprocessed, "updated_blocks", "updated_support_blocks", track=True)

    prescribed_displacements = postprocessed.metadata.get("prescribed_displacements", [])
    if prescribed_displacement_scale is None:
        maximum_displacement = max(
            (_length(item.get("displacement", [0.0, 0.0, 0.0])) for item in prescribed_displacements),
            default=0.0,
        )
        maximum_length = float(force_length_ratio) * _block_size(analysis, model_size)
        prescribed_displacement_scale = maximum_length / maximum_displacement if maximum_displacement > 1e-30 else 1.0

    for item in prescribed_displacements:
        vector = item.get("displacement", [0.0, 0.0, 0.0])
        magnitude = _length(vector)
        for node in item.get("blocks", []):
            point = block_centroids.get(node)
            if point is None:
                continue
            lines = _arrow_lines(point, vector, prescribed_displacement_scale, model_size)
            if not lines:
                continue
            geometry["prescribed_displacement_lines"].extend(lines)
            geometry["prescribed_displacement_points"].append(Point(*point))
            geometry["prescribed_displacement_labels"].append(
                {
                    "point": Point(*lines[0].end),
                    "text": "{:.{}f} m".format(magnitude, int(displacement_label_decimals)),
                }
            )

    for load in postprocessed.metadata.get("applied_loads", []):
        points = []
        visual_force = load["force"]
        surface_label_point = None
        if load["kind"] == "surface_stress":
            # Show the distributed traction at the face vertices and centroid.
            # Dividing the resultant among the glyphs keeps their combined
            # visual scale consistent with point and reaction forces.
            points = [list(point) for point in load.get("face_vertices", [])]
            points.append(list(load["face_center"]))
            transformation = block_transformations.get(load.get("block"))
            if transformation is not None:
                transformed = []
                for coordinates in points:
                    point = Point(*coordinates)
                    point.transform(transformation)
                    transformed.append(list(point))
                points = transformed
            surface_label_point = Point(*points[-1])
            count = max(len(points), 1)
            visual_force = [float(value) / count for value in load["force"]]
        elif load["kind"] == "sphere":
            point = Point(*load["point"])
            transformation = block_transformations.get(load.get("block"))
            if transformation is not None:
                point.transform(transformation)
            points.append(list(point))
        else:
            points.extend(block_centroids[node] for node in load.get("blocks", []) if node in block_centroids)
        for point in points:
            line = _line(point, visual_force, force_scale)
            if line is None:
                continue
            geometry["applied_load_lines"].append(line)
            geometry["applied_load_points"].append(Point(*point))
            if load["kind"] != "surface_stress":
                geometry["applied_load_labels"].append(
                    {
                        "point": Point(*line.end),
                        "text": "{:.{}f} {}".format(
                            _length(visual_force) * float(reaction_force_factor),
                            int(reaction_label_decimals),
                            reaction_force_unit,
                        ),
                    }
                )
        if surface_label_point is not None:
            geometry["applied_load_labels"].append(
                {
                    "point": surface_label_point,
                    "text": "{:.{}f} kN/m²".format(
                        _length(load["traction"]) * 0.001,
                        int(reaction_label_decimals),
                    ),
                }
            )

    support_nodes = set(analysis.supports)

    for contact in postprocessed.contacts:
        if contact.get("geometry") is not None:
            geometry["contact_geometry"].append(contact["geometry"])
        geometry["resultant_points"].append(Point(*contact["resultant_point"]))
        geometry["normal_application_points"].append(Point(*contact["normal_application_point"]))
        geometry["shear_application_points"].append(Point(*contact["shear_application_point"]))

        force_pairs = (
            ("resultant_force_lines", contact["resultant_point"], contact["resultant_force"], force_scale),
            ("resultant_normal_lines", contact["resultant_point"], contact["resultant_normal"], force_scale),
            ("resultant_shear_lines", contact["shear_application_point"], contact["resultant_shear"], force_scale),
            ("transported_shear_lines", contact["resultant_point"], contact["resultant_shear"], force_scale),
        )
        for category, point, vector, scale in force_pairs:
            geometry[category].extend(_action_reaction_lines(point, vector, scale))

        edge = list(contact.get("edge") or [])
        supported = [node for node in edge if node in support_nodes]
        free = [node for node in edge if node not in support_nodes]
        if len(supported) == 1 and len(free) == 1:
            support_node = supported[0]
            free_node = free[0]
            vector = list(contact["resultant_force"])
            toward_support = [block_centroids[support_node][index] - block_centroids[free_node][index] for index in range(3)]
            if _dot(vector, toward_support) < 0.0:
                vector = [-value for value in vector]
            point = contact["resultant_point"]
            reaction_lines = _arrow_lines(point, vector, force_scale, model_size)
            geometry["reaction_force_lines"].extend(reaction_lines)
            geometry["reaction_points"].append(Point(*point))

            if reaction_label_mode not in (None, "magnitude", "components"):
                raise ValueError("reaction_label_mode must be 'magnitude', 'components', or None.")
            if reaction_label_mode:
                converted = [value * reaction_force_factor for value in vector]
                magnitude_text = "{:.{}f} {}".format(
                    _length(converted),
                    int(reaction_label_decimals),
                    reaction_force_unit,
                )
                component_text = "Fx={0:.{3}f}, Fy={1:.{3}f}, Fz={2:.{3}f} {4}".format(
                    converted[0],
                    converted[1],
                    converted[2],
                    int(reaction_label_decimals),
                    reaction_force_unit,
                )
                label_point = reaction_lines[0].end if reaction_lines else Point(*point)
                magnitude_label = {"point": Point(*label_point), "text": magnitude_text}
                component_label = {"point": Point(*label_point), "text": component_text}
                geometry["reaction_magnitude_labels"].append(magnitude_label)
                geometry["reaction_component_labels"].append(component_label)
                geometry["reaction_labels"].append(magnitude_label if reaction_label_mode == "magnitude" else component_label)

        geometry["torque_lines"].extend(
            _action_reaction_lines(
                contact["resultant_point"],
                contact["torque_at_normal_point"],
                torque_scale,
            )
        )

        shear = contact["resultant_shear"]
        shear_length = _length(shear)
        if shear_length > 1e-30:
            direction = [value / shear_length for value in shear]
            point = contact["shear_application_point"]
            local_length = line_of_action_length
            if local_length is None:
                local_length = 0.8 * _interface_size(
                    contact.get("geometry"),
                    0.1 * model_size,
                )
            half = 0.5 * local_length
            geometry["shear_lines_of_action"].append(
                Line(
                    [point[index] - direction[index] * half for index in range(3)],
                    [point[index] + direction[index] * half for index in range(3)],
                )
            )

        geometry["crack_points"].extend(Point(*point) for point in contact["opening_points"])
        geometry["hinge_points"].extend(Point(*point) for point in contact["hinge_points"])
        for subcontact in contact["subcontacts"]:
            point = subcontact["point"]
            geometry["subcontact_points"].append(Point(*point))
            normal_lines = _action_reaction_lines(point, subcontact["force_normal_vector"], force_scale)
            shear_lines = _action_reaction_lines(point, subcontact["force_shear"], force_scale)
            opening_line = _line(point, subcontact["opening_vector"], displacement_scale)
            geometry["normal_force_lines"].extend(normal_lines)
            geometry["shear_force_lines"].extend(shear_lines)
            if subcontact["open"] and opening_line is not None:
                geometry["opening_lines"].append(opening_line)
            if subcontact["sliding"]:
                category = "friction_sliding_points"
            elif subcontact.get("friction_limit_reached"):
                category = "friction_limit_points"
            else:
                category = "friction_safe_points"
            geometry[category].append(Point(*point))
    return geometry
