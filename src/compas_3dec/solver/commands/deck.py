def _number(value):
    return "{:.12g}".format(float(value))


def _value(item, name, default=None):
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _quote(value):
    return "'{}'".format(str(value).replace("'", "''"))


def _material_commands(analysis):
    lines = ["; Block material properties"]
    grouped = {}
    for block in analysis.blocks:
        grouped.setdefault(block.get("group", "block"), []).append(block)
    for group, blocks in sorted(grouped.items()):
        densities = []
        for block in blocks:
            material = block.get("material")
            density = _value(material, "density") if material is not None else None
            if density is None:
                raise ValueError("Block at graph node {} has no material density.".format(block["node"]))
            densities.append(float(density))
        if len(set(densities)) == 1:
            lines.append(
                "block property density {} range group {}".format(
                    _number(densities[0]),
                    _quote(group),
                )
            )
            continue
        # Imported DEM models may contain per-block materials before DEM gains
        # explicit group support. Preserve them using stable region selection.
        for block, density in sorted(zip(blocks, densities), key=lambda item: item[0]["region"]):
            lines.append("block property density {} range region {}".format(_number(density), block["region"]))
    return lines


def _contact_values(properties):
    if properties is None:
        raise ValueError("The analysis has no contact properties.")

    joint_model = _value(properties, "joint_model")
    kn = _value(properties, "stiffness_normal")
    kt = _value(properties, "stiffness_shear")
    if joint_model is not None:
        kn = _value(joint_model, "kn", kn)
        kt = _value(joint_model, "kt", kt)
    if kn is None or kt is None:
        raise ValueError("3DEC requires contact normal and tangential stiffness (kn and kt).")

    contact_model = _value(properties, "contact_model")
    friction = _value(properties, "friction")
    if contact_model is not None:
        friction = _value(contact_model, "phi", friction)
    if friction is None:
        raise ValueError("3DEC requires a contact friction angle.")

    cohesion = _value(properties, "cohesion")
    tension = _value(properties, "tension")
    if contact_model is not None:
        cohesion = _value(contact_model, "c", cohesion)
        tension = _value(contact_model, "t_c", tension)
    parts = [
        "stiffness-normal {}".format(_number(kn)),
        "stiffness-shear {}".format(_number(kt)),
        "friction {}".format(_number(friction)),
    ]
    if cohesion is not None:
        parts.append("cohesion {}".format(_number(cohesion)))
    if tension is not None:
        parts.append("tension {}".format(_number(tension)))
    return " ".join(parts)


def _contact_commands(analysis):
    values = _contact_values(analysis.contact_properties)
    lines = [
        "block contact generate-subcontacts",
        "block contact property {}".format(values),
        "block contact material-table default property {}".format(values),
    ]
    group_table_entries = []
    for override in analysis.contact_property_overrides:
        group_a = _quote(override["group_a"])
        group_b = _quote(override["group_b"])
        override_values = _contact_values(override["properties"])
        contact_range = "range group-intersection {} {}".format(group_a, group_b)
        lines.append("block contact property {} {}".format(override_values, contact_range))
        group_table_entries.append("block contact material-table add jmodel mohr property {} {}".format(override_values, contact_range))
    block_pair_table_entries = []
    for override in analysis.contact_block_pair_overrides:
        identity_a = _quote("COMPAS_ID=COMPAS_NODE_{}".format(override["node_a"]))
        identity_b = _quote("COMPAS_ID=COMPAS_NODE_{}".format(override["node_b"]))
        override_values = _contact_values(override["properties"])
        contact_range = "range group-intersection {} {}".format(identity_a, identity_b)
        lines.append("block contact property {} {}".format(override_values, contact_range))
        block_pair_table_entries.append("block contact material-table add jmodel mohr property {} {}".format(override_values, contact_range))
    # Specific exact-pair entries precede broader group-pair entries in the
    # material table. Existing-contact exact-pair commands already occur last.
    lines.extend(block_pair_table_entries)
    lines.extend(group_table_entries)
    return lines


def _support_commands(stage_plan):
    return ["block fix range region {}".format(node) for node in stage_plan.supports]


def _gravity_commands(stage):
    steps = int(stage.options.get("gravity_steps", 10))
    if steps <= 0:
        raise ValueError("gravity_steps must be a positive integer.")

    gravity = -abs(float(stage.gravity))
    ratio = float(stage.options.get("ratio", 1e-5))
    keyword = str(stage.options.get("ratio_keyword", "ratio-local"))
    solve_time = float(stage.options.get("time", 1.0))

    lines = ["; Gravity stage"]
    for index in range(steps):
        value = gravity * float(index + 1) / float(steps)
        lines.append("model gravity 0 0 {}".format(_number(value)))
        lines.append(
            "model solve {} {} time {}".format(
                keyword,
                _number(ratio),
                _number(solve_time),
            )
        )
    return lines


def _load_commands(
    analysis,
    stage,
    fish_dialect,
    final_results_filename,
    final_save_filename="load-final.sav",
    file_prefix="load",
):
    loads = list(stage.point_loads or [])
    surface_loads = list(stage.surface_loads or [])
    if stage.body_forces:
        raise NotImplementedError("Body load rendering will be implemented separately.")
    if not loads and not surface_loads:
        return []

    maximum_steps = max(int(load["steps"]) for load in loads + surface_loads)
    ratio = float(stage.options.get("ratio", 1e-5))
    keyword = str(stage.options.get("ratio_keyword", "ratio-local"))
    cycles = stage.options.get("cycles")
    solve_time = stage.options.get("solve_time")
    save_steps = bool(stage.options.get("save_steps", True))
    stop_on_nonconvergence = bool(stage.options.get("stop_on_nonconvergence", True))
    lines = ["; Synchronized point and surface-load stage"]

    for step in range(1, maximum_steps + 1):
        lines.extend(["", "; Load step {} of {}".format(step, maximum_steps)])

        # 3DEC adds permanent ``block gridpoint apply force`` conditions to
        # the existing load. Therefore write one constant increment at every
        # active step. Writing cumulative values here would sum the triangular
        # load history and severely over-apply the requested force.
        for load_index, load in enumerate(loads):
            if load["kind"] != "sphere" or step > int(load["steps"]):
                continue
            increment = float(load["magnitude"]) / float(load["steps"])
            per_gridpoint = increment / int(load.get("distribution_count", 1))
            vector = [per_gridpoint * float(value) for value in load["direction"]]
            point = load["point"]
            command = ("block gridpoint apply force-x {} force-y {} force-z {} range sphere c {} {} {} r {}").format(
                _number(vector[0]),
                _number(vector[1]),
                _number(vector[2]),
                _number(point[0]),
                _number(point[1]),
                _number(point[2]),
                _number(load["radius"]),
            )
            if load.get("block") is not None:
                region = analysis.entity_map.region_for_node(int(load["block"]))
                command += " region {}".format(region)
            lines.append(command)
            lines.append(
                "; load {} increment {}, cumulative {}".format(
                    load_index,
                    _number(float(load["magnitude"]) / float(load["steps"])),
                    _number(float(load["magnitude"]) * min(step, int(load["steps"])) / float(load["steps"])),
                )
            )

        # Centroid loads are assigned as cumulative rigid-block forces. Sum
        # multiple loads targeting the same block before writing block.force.app.
        centroid_vectors = {}
        for load in loads:
            if load["kind"] != "centroid":
                continue
            applied = min(step, int(load["steps"])) / float(load["steps"])
            nodes = list(load["blocks"])
            for node in nodes:
                vector = centroid_vectors.setdefault(int(node), [0.0, 0.0, 0.0])
                for index in range(3):
                    vector[index] += float(load["magnitude"]) * applied * float(load["direction"][index])
        if centroid_vectors:
            function = "compas_3dec_centroid_load_{}".format(step)
            lines.append("fish define {}".format(function))
            lines.append("    loop foreach local ib block.list")
            for node, vector in sorted(centroid_vectors.items()):
                region = analysis.entity_map.region_for_node(node)
                lines.append("        if block.region(ib) = {} then".format(region))
                lines.append("            block.force.app(ib) = vector({},{},{})".format(_number(vector[0]), _number(vector[1]), _number(vector[2])))
                lines.append("        endif")
            lines.extend(["    endloop", "end", "@{}".format(function)])

        # 3DEC adds repeated face-stress commands to the existing boundary
        # traction. Apply one equal tensor increment while each load is active.
        for load_index, load in enumerate(surface_loads):
            if step > int(load["steps"]):
                continue
            increment = [float(value) / float(load["steps"]) for value in load["stress"]]
            xx, yy, zz, xy, yz, zx = increment
            vertices = load["face_vertices"]
            tolerance = float(load.get("range_tolerance", 1e-9))
            bounds = []
            for axis in range(3):
                values = [float(vertex[axis]) for vertex in vertices]
                bounds.extend((min(values) - tolerance, max(values) + tolerance))
            region = analysis.entity_map.region_for_node(int(load["block"]))
            lines.append(
                "block face apply stress {} {} {} {} {} {} range position-x {} {} position-y {} {} position-z {} {} region {}".format(
                    _number(xx), _number(yy), _number(zz), _number(xy), _number(zx), _number(yz), *[_number(value) for value in bounds], region
                )
            )
            lines.append("; surface load {} tensor increment".format(load_index))

        solve = "model solve {} {}".format(keyword, _number(ratio))
        if cycles is not None:
            solve += " or cycles {}".format(int(cycles))
        if solve_time is not None:
            solve += " or time {}".format(_number(solve_time))
        lines.append(solve)
        if save_steps:
            cumulative_total = sum(float(load["magnitude"]) * min(step, int(load["steps"])) / float(load["steps"]) for load in loads) + sum(
                float(load.get("face_area", 0.0))
                * sum(float(value) ** 2 for value in load.get("traction", [0, 0, 0])) ** 0.5
                * min(step, int(load["steps"]))
                / float(load["steps"])
                for load in surface_loads
            )
            stem = "{}-step-{:04d}-{}N".format(
                file_prefix,
                step,
                int(round(cumulative_total)),
            )
            lines.append(fish_dialect.capture_results("results-{}.txt".format(stem)))
            lines.append("model save './{}.sav' compress".format(stem))
        if stop_on_nonconvergence:
            # Always leave a parseable final snapshot before the legacy-style
            # equilibrium guard can terminate the 3DEC program.
            lines.append(fish_dialect.capture_results(final_results_filename))
            lines.append("model save './{}' compress".format(final_save_filename))
            function = "compas_3dec_check_equilibrium_{}".format(step)
            lines.extend(
                [
                    "fish define {}".format(function),
                    "    if mech.solve('{}') > {} then".format(
                        keyword.replace("'", "''"),
                        _number(ratio),
                    ),
                    "        system.command('exit')",
                    "    endif",
                    "end",
                    "@{}".format(function),
                ]
            )
    return lines


def render_analysis_deck(
    analysis,
    stage_plan,
    fish_dialect,
    geometry_filename="geometry.dat",
    initial_results_filename="results-initial.txt",
    gravity_results_filename="results-gravity.txt",
    final_results_filename="results-final.txt",
):
    """Render the initialisation and gravity analysis deck."""
    lines = [
        "; Generated by compas_3dec",
        "model new",
        "model precision 15",
        "model large-strain on",
        "program call '{}'".format(geometry_filename),
    ]
    lines.extend(_material_commands(analysis))
    lines.extend(_contact_commands(analysis))
    lines.extend(_support_commands(stage_plan))
    lines.append("block mechanical damping global")
    lines.append(fish_dialect.definitions())
    lines.append(fish_dialect.capture_results(initial_results_filename))
    lines.append("model save './initial.sav' compress")

    gravity = stage_plan.stage("gravity")
    if gravity is not None:
        lines.extend(_gravity_commands(gravity))
        lines.append("model save './gravity.sav' compress")
        lines.append(fish_dialect.capture_results(gravity_results_filename))
    lines.append(fish_dialect.capture_results(final_results_filename))
    if gravity is None:
        lines.append("model save './initial.sav' compress")
    lines.append("program exit")
    return "\n".join(lines) + "\n"


def render_load_deck(
    analysis,
    stage_plan,
    fish_dialect,
    final_results_filename="results-final.txt",
    stage=None,
    restore_filename="gravity.sav",
    final_save_filename="load-final.sav",
    file_prefix="load",
):
    """Render one load phase starting from the preceding saved state."""
    loads = stage or stage_plan.stage("loads")
    if loads is None:
        return None
    if stage_plan.stage("gravity") is None:
        raise ValueError("Point-load stages require a gravity stage and gravity.sav checkpoint.")
    damping = str(loads.options.get("damping", "global")).strip().lower()
    if damping not in ("global", "local", "combined"):
        raise ValueError("Load damping must be 'global', 'local', or 'combined'.")
    lines = [
        "; Generated by compas_3dec: point-load stage",
        "model restore './{}'".format(restore_filename),
        "block mechanical damping {}".format(damping),
        fish_dialect.definitions(),
    ]
    lines.extend(
        _load_commands(
            analysis,
            loads,
            fish_dialect,
            final_results_filename,
            final_save_filename,
            file_prefix,
        )
    )
    lines.append(fish_dialect.capture_results(final_results_filename))
    lines.append("model save './{}' compress".format(final_save_filename))
    lines.append("program exit")
    return "\n".join(lines) + "\n"


def render_displacement_deck(
    analysis,
    stage_plan,
    fish_dialect,
    restore_filename,
    final_results_filename="results-final.txt",
    stage=None,
    final_save_filename="displacement-final.sav",
    file_prefix="displacement",
):
    """Render cumulative rigid-block translations followed by equilibrium."""
    stage = stage or stage_plan.stage("displacements")
    if stage is None:
        return None
    displacements = list(stage.displacements or [])
    if not displacements:
        return None
    if stage_plan.stage("gravity") is None:
        raise ValueError("Displacement stages require a completed gravity state.")
    damping = str(stage.options.get("damping", "local")).strip().lower()
    if damping not in ("global", "local", "combined"):
        raise ValueError("Displacement damping must be 'global', 'local', or 'combined'.")
    motion_time = float(stage.options.get("motion_time", 1.0))
    if motion_time <= 0.0:
        raise ValueError("Displacement motion_time must be positive.")
    ratio = float(stage.options.get("ratio", 1e-5))
    keyword = str(stage.options.get("ratio_keyword", "ratio-local"))
    equilibrium_cycles = stage.options.get("equilibrium_cycles", 15000)
    equilibrium_time = stage.options.get("equilibrium_time")
    save_steps = bool(stage.options.get("save_steps", True))
    stop_on_nonconvergence = bool(stage.options.get("stop_on_nonconvergence", True))
    maximum_steps = max(int(item["steps"]) for item in displacements)
    targeted = {}
    for item in displacements:
        for node in item["blocks"]:
            mask = targeted.setdefault(int(node), [False, False, False])
            for index, active in enumerate(item.get("active_components", [True, True, True])):
                mask[index] = mask[index] or bool(active)

    lines = [
        "; Generated by compas_3dec: displacement stage",
        "model restore './{}'".format(restore_filename),
        "block mechanical damping {}".format(damping),
        fish_dialect.definitions(),
    ]
    for step in range(1, maximum_steps + 1):
        lines.extend(["", "; Displacement step {} of {}".format(step, maximum_steps)])
        increments = {}
        masks = {}
        for item in displacements:
            if step > int(item["steps"]):
                continue
            increment = float(item["magnitude"]) / float(item["steps"])
            for node in item["blocks"]:
                vector = increments.setdefault(int(node), [0.0, 0.0, 0.0])
                mask = masks.setdefault(int(node), [False, False, False])
                for index in range(3):
                    vector[index] += increment * float(item["direction"][index])
                    mask[index] = mask[index] or bool(item.get("active_components", [True, True, True])[index])

        cycle_variable = "compas_3dec_displacement_cycles_{}".format(step)
        time_variable = "compas_3dec_displacement_time_{}".format(step)
        lines.append("[global {} = math.ceil({} / mech.timestep)]".format(cycle_variable, _number(motion_time)))
        lines.append("[global {} = {} * mech.timestep]".format(time_variable, cycle_variable))
        for node, vector in sorted(increments.items()):
            region = analysis.entity_map.region_for_node(node)
            for index, axis in enumerate("xyz"):
                if not masks[node][index]:
                    continue
                lines.append("block apply velocity-{} [{}/{}] range region {}".format(axis, _number(vector[index]), time_variable, region))
        lines.append("model cycle [{}]".format(cycle_variable))

        lines.append("; Stop prescribed motion before checking equilibrium")
        for node, mask in sorted(targeted.items()):
            region = analysis.entity_map.region_for_node(node)
            for index, axis in enumerate("xyz"):
                if mask[index]:
                    lines.append("block apply velocity-{} 0 range region {}".format(axis, region))
        solve = "model solve {} {}".format(keyword, _number(ratio))
        if equilibrium_cycles is not None:
            solve += " or cycles {}".format(int(equilibrium_cycles))
        if equilibrium_time is not None:
            solve += " or time {}".format(_number(equilibrium_time))
        lines.append(solve)

        cumulative = sum(float(item["magnitude"]) * min(step, int(item["steps"])) / float(item["steps"]) for item in displacements)
        stem = "{}-step-{:04d}-{}um".format(
            file_prefix,
            step,
            int(round(cumulative * 1e6)),
        )
        if save_steps:
            lines.append(fish_dialect.capture_results("results-{}.txt".format(stem)))
            lines.append("model save './{}.sav' compress".format(stem))
        if stop_on_nonconvergence:
            lines.append(fish_dialect.capture_results(final_results_filename))
            lines.append("model save './{}' compress".format(final_save_filename))
            function = "compas_3dec_check_displacement_equilibrium_{}".format(step)
            lines.extend(
                [
                    "fish define {}".format(function),
                    "    if mech.solve('{}') > {} then".format(keyword.replace("'", "''"), _number(ratio)),
                    "        system.command('exit')",
                    "    endif",
                    "end",
                    "@{}".format(function),
                ]
            )
    lines.append(fish_dialect.capture_results(final_results_filename))
    lines.append("model save './{}' compress".format(final_save_filename))
    lines.append("program exit")
    return "\n".join(lines) + "\n"
