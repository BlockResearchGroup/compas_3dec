from compas_3dec.postprocessing import postprocess_raw_results

from .visualisation import build_visualisation


def draw_results(
    analysis,
    raw_results,
    postprocessed=None,
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
    clear_existing=False,
):
    """Draw native 3DEC result geometry in the active Rhino document.

    Returns a dictionary of Rhino GUID lists keyed by result category. By
    default, objects from an earlier call below the ``3DEC Results`` layer are
    deleted before the selected state is drawn. Unrelated document objects are
    not touched. The function imports Rhino only when called, so the module
    remains importable in normal CPython.
    """
    try:
        import Rhino  # type: ignore
        import scriptcontext as sc  # type: ignore
        from compas_rhino.conversions import line_to_rhino
        from compas_rhino.conversions import mesh_to_rhino
        from compas_rhino.conversions import point_to_rhino
        from System.Drawing import Color as DrawingColor  # type: ignore

        from compas.datastructures import Mesh
        from compas.geometry import Line
        from compas.geometry import Point
        from compas.geometry import Polygon
    except ImportError as error:
        raise RuntimeError("draw_results must be called inside Rhino.") from error

    postprocessed = postprocessed or postprocess_raw_results(analysis, raw_results)
    result_state = str(postprocessed.metadata.get("result_state") or "updated")
    state_label = result_state.replace("-", " ").title()

    if clear_existing:
        result_layers = [layer for layer in sc.doc.Layers if not layer.IsDeleted and (layer.FullPath == "3DEC Results" or layer.FullPath.startswith("3DEC Results::"))]
        for layer in result_layers:
            for rhino_object in sc.doc.Objects.FindByLayer(layer) or []:
                sc.doc.Objects.Delete(rhino_object.Id, True)

    visual = build_visualisation(
        analysis,
        postprocessed,
        gravity_postprocessed=gravity_postprocessed,
        force_scale=force_scale,
        torque_scale=torque_scale,
        displacement_scale=displacement_scale,
        line_of_action_length=line_of_action_length,
        reaction_label_mode=reaction_label_mode,
        reaction_force_factor=reaction_force_factor,
        reaction_force_unit=reaction_force_unit,
        reaction_label_decimals=reaction_label_decimals,
        force_length_ratio=force_length_ratio,
        prescribed_displacement_scale=prescribed_displacement_scale,
        displacement_label_decimals=displacement_label_decimals,
    )

    def force_name(prefix, vector):
        magnitude = sum(float(value) ** 2 for value in vector) ** 0.5
        magnitude *= float(reaction_force_factor)
        return "{}: {:.{}f} {}".format(
            prefix,
            magnitude,
            int(reaction_label_decimals),
            reaction_force_unit,
        )

    object_names = {
        "resultant_force_lines": [force_name("Resultant force", contact["resultant_force"]) for contact in postprocessed.contacts for _ in range(2)],
        "reaction_force_lines": [
            force_name("Support reaction", contact["resultant_force"])
            for contact in postprocessed.contacts
            if len([node for node in contact.get("edge", []) if node in analysis.supports]) == 1
            and len([node for node in contact.get("edge", []) if node not in analysis.supports]) == 1
            for _ in range(3)
        ],
        "applied_load_lines": [
            force_name("Applied load", load["force"])
            for load in postprocessed.metadata.get("applied_loads", [])
            for _ in (load.get("blocks", []) if load["kind"] == "centroid" else [None])
        ],
        "prescribed_displacement_lines": [
            "Prescribed displacement: {:.{}f} m".format(
                sum(float(value) ** 2 for value in item.get("displacement", [])) ** 0.5,
                int(displacement_label_decimals),
            )
            for item in postprocessed.metadata.get("prescribed_displacements", [])
            for _node in item.get("blocks", [])
            for _ in range(3)
        ],
    }
    colours = {
        "initial_blocks": (150, 150, 150),
        "gravity_blocks": (205, 205, 205),
        "gravity_support_blocks": (125, 160, 205),
        "updated_blocks": (180, 180, 180),
        "updated_support_blocks": (76, 120, 168),
        "contact_geometry": (0, 200, 220),
        "subcontact_points": (100, 100, 100),
        "normal_force_lines": (30, 100, 240),
        "shear_force_lines": (240, 140, 20),
        "resultant_force_lines": (220, 30, 30),
        "resultant_points": (220, 30, 30),
        "resultant_normal_lines": (30, 100, 240),
        "resultant_shear_lines": (240, 140, 20),
        "transported_shear_lines": (180, 90, 10),
        "torque_lines": (220, 40, 220),
        "shear_lines_of_action": (220, 40, 220),
        "normal_application_points": (30, 100, 240),
        "shear_application_points": (240, 140, 20),
        "friction_safe_points": (30, 180, 70),
        "friction_limit_points": (245, 170, 20),
        "friction_sliding_points": (230, 20, 20),
        "crack_points": (230, 20, 20),
        "opening_lines": (230, 20, 20),
        "hinge_points": (220, 40, 220),
        "reaction_force_lines": (30, 170, 60),
        "reaction_points": (30, 170, 60),
        "reaction_labels": (30, 170, 60),
        "reaction_magnitude_labels": (30, 170, 60),
        "reaction_component_labels": (30, 170, 60),
        "applied_load_lines": (145, 70, 200),
        "applied_load_points": (145, 70, 200),
        "applied_load_labels": (145, 70, 200),
        "prescribed_displacement_lines": (0, 145, 210),
        "prescribed_displacement_points": (0, 145, 210),
        "prescribed_displacement_labels": (0, 145, 210),
    }
    layers = {
        "initial_blocks": "3DEC Results::Geometry::Initial",
        "gravity_blocks": "3DEC Results::Geometry::Gravity::Blocks",
        "gravity_support_blocks": "3DEC Results::Geometry::Gravity::Supports",
        "updated_blocks": "3DEC Results::Geometry::{}::Blocks".format(state_label),
        "updated_support_blocks": "3DEC Results::Geometry::{}::Supports".format(state_label),
        "contact_geometry": "3DEC Results::Interfaces::Geometry",
        "subcontact_points": "3DEC Results::Interfaces::Subcontacts::Points",
        "normal_force_lines": "3DEC Results::Forces::Subcontacts::Normal",
        "shear_force_lines": "3DEC Results::Forces::Subcontacts::Shear",
        "resultant_force_lines": "3DEC Results::Forces::Resultants::Total",
        "resultant_normal_lines": "3DEC Results::Forces::Resultants::Normal",
        "resultant_shear_lines": "3DEC Results::Forces::Resultants::Shear at Shear Point",
        "transported_shear_lines": "3DEC Results::Forces::Resultants::Shear Transported to Resultant Point",
        "resultant_points": "3DEC Results::Forces::Application Points::Resultant",
        "normal_application_points": "3DEC Results::Forces::Application Points::Normal Axis",
        "shear_application_points": "3DEC Results::Forces::Application Points::Shear Axis",
        "torque_lines": "3DEC Results::Moments::Residual Torque",
        "shear_lines_of_action": "3DEC Results::Moments::Shear Lines of Action",
        "friction_safe_points": "3DEC Results::Interface State::Friction::Safe",
        "friction_limit_points": "3DEC Results::Interface State::Friction::Limit Reached, No Confirmed Slip",
        "friction_sliding_points": "3DEC Results::Interface State::Friction::Confirmed Sliding",
        "crack_points": "3DEC Results::Interface State::Opening::Open Points",
        "opening_lines": "3DEC Results::Interface State::Opening::Displacement",
        "hinge_points": "3DEC Results::Interface State::Opening::Hinge Candidates",
        "reaction_force_lines": "3DEC Results::Reactions::Support Reactions::Vectors",
        "reaction_points": "3DEC Results::Reactions::Support Reactions::Application Points",
        "reaction_labels": "3DEC Results::Reactions::Support Reactions::Labels",
        "reaction_magnitude_labels": "3DEC Results::Reactions::Support Reactions::Labels::Magnitude",
        "reaction_component_labels": "3DEC Results::Reactions::Support Reactions::Labels::Components (Fx, Fy, Fz)",
        "applied_load_lines": "3DEC Results::Loads::Applied Loads::Vectors",
        "applied_load_points": "3DEC Results::Loads::Applied Loads::Application Points",
        "applied_load_labels": "3DEC Results::Loads::Applied Loads::Labels",
        "prescribed_displacement_lines": "3DEC Results::Displacements::Prescribed::Vectors",
        "prescribed_displacement_points": "3DEC Results::Displacements::Prescribed::Block Centroids",
        "prescribed_displacement_labels": "3DEC Results::Displacements::Prescribed::Labels",
    }
    initially_visible = {
        "gravity_blocks",
        "gravity_support_blocks",
        "updated_blocks",
        "updated_support_blocks",
        "resultant_force_lines",
        "resultant_points",
        "reaction_force_lines",
        "reaction_points",
        "reaction_labels",
        "reaction_magnitude_labels",
        "applied_load_lines",
        "applied_load_points",
        "applied_load_labels",
        "prescribed_displacement_lines",
        "prescribed_displacement_points",
        "prescribed_displacement_labels",
    }
    output = {key: [] for key in visual}

    def layer_index(path, colour, category):
        parent_id = System.Guid.Empty
        index = -1
        names = path.split("::")
        for position, name in enumerate(names):
            existing = next(
                (layer for layer in sc.doc.Layers if not layer.IsDeleted and layer.Name == name and layer.ParentLayerId == parent_id),
                None,
            )
            if existing is None:
                layer = Rhino.DocObjects.Layer()
                layer.Name = name
                layer.ParentLayerId = parent_id
                index = sc.doc.Layers.Add(layer)
                existing = sc.doc.Layers[index]
            else:
                index = existing.Index
            if position == len(names) - 1:
                existing.Color = DrawingColor.FromArgb(*colour)
                existing.IsVisible = category in initially_visible
                existing.CommitChanges()
            parent_id = existing.Id
        return index

    import System  # type: ignore

    layer_indices = {category: layer_index(path, colours.get(category, (0, 0, 0)), category) for category, path in layers.items()}

    def attributes(category, index):
        attr = Rhino.DocObjects.ObjectAttributes()
        names = object_names.get(category, [])
        attr.Name = names[index] if index < len(names) else "3DEC_{}_{}".format(category, index)
        attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer
        attr.LayerIndex = layer_indices[category]
        if category in ("reaction_force_lines", "applied_load_lines", "prescribed_displacement_lines"):
            attr.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.EndArrowhead
        return attr

    redraw_was_enabled = sc.doc.Views.RedrawEnabled
    sc.doc.Views.RedrawEnabled = False
    try:
        for category, items in visual.items():
            # Backward-compatible aggregate; Rhino draws the two independently
            # switchable label categories below instead.
            if category == "reaction_labels":
                continue
            if not items:
                continue
            for index, item in enumerate(items):
                # The backend-neutral reaction arrow contains one shaft followed
                # by two geometric arrowhead segments. Rhino uses its clearer
                # native curve decoration, so only add each shaft here.
                if category in ("reaction_force_lines", "prescribed_displacement_lines") and index % 3:
                    continue
                attr = attributes(category, index)
                if isinstance(item, Mesh):
                    guid = sc.doc.Objects.AddMesh(mesh_to_rhino(item, disjoint=False), attr)
                elif isinstance(item, Line):
                    guid = sc.doc.Objects.AddLine(line_to_rhino(item), attr)
                elif isinstance(item, Point):
                    guid = sc.doc.Objects.AddPoint(point_to_rhino(item), attr)
                elif isinstance(item, Polygon):
                    points = [Rhino.Geometry.Point3d(*point) for point in item.points]
                    points.append(points[0])
                    guid = sc.doc.Objects.AddPolyline(points, attr)
                elif category in (
                    "reaction_labels",
                    "reaction_magnitude_labels",
                    "reaction_component_labels",
                    "applied_load_labels",
                    "prescribed_displacement_labels",
                ) and isinstance(item, dict):
                    text_dot = Rhino.Geometry.TextDot(
                        item["text"],
                        Rhino.Geometry.Point3d(*item["point"]),
                    )
                    guid = sc.doc.Objects.AddTextDot(text_dot, attr)
                else:
                    continue
                if guid:
                    output[category].append(guid)
    finally:
        sc.doc.Views.RedrawEnabled = redraw_was_enabled
        if redraw_was_enabled:
            sc.doc.Views.Redraw()
    return output
