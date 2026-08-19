import json
from pathlib import Path

import compas

from .io import parse_results_file


def applied_loads_at_step(loads, step):
    """Return the cumulative applied loads at a synchronized load step."""
    output = []
    for load in loads:
        fraction = min(int(step), int(load["steps"])) / float(load["steps"])
        if load.get("kind") == "surface_stress":
            traction = [fraction * float(value) for value in load["traction"]]
            output.append(
                {
                    "kind": "surface_stress",
                    "name": load.get("name"),
                    "block": load["block"],
                    "face": load["face"],
                    "stress": [fraction * float(value) for value in load["stress"]],
                    "traction": traction,
                    "force": [float(load["face_area"]) * value for value in traction],
                    "face_area": load["face_area"],
                    "face_center": list(load["face_center"]),
                    "face_vertices": [list(vertex) for vertex in load["face_vertices"]],
                    "capacity": bool(load.get("capacity", False)),
                    "capacity_increment": load.get("capacity_increment"),
                }
            )
            continue
        magnitude = float(load["magnitude"]) * fraction
        item = {
            "kind": load["kind"],
            "name": load.get("name"),
            "magnitude": magnitude,
            "direction": list(load["direction"]),
            "force": [magnitude * float(value) for value in load["direction"]],
            "capacity": bool(load.get("capacity", False)),
            "capacity_increment": load.get("capacity_increment"),
        }
        if load["kind"] == "sphere":
            item.update(point=list(load["point"]), block=load.get("block"))
        else:
            item["blocks"] = list(load["blocks"])
        output.append(item)
    return output


def prescribed_displacements_at_step(displacements, step):
    """Return cumulative prescribed translations at one synchronized step."""
    output = []
    for item in displacements:
        fraction = min(int(step), int(item["steps"])) / float(item["steps"])
        magnitude = float(item["magnitude"]) * fraction
        output.append(
            {
                "kind": "translation",
                "name": item.get("name"),
                "blocks": list(item["blocks"]),
                "magnitude": magnitude,
                "direction": list(item["direction"]),
                "displacement": [magnitude * float(value) for value in item["direction"]],
                "capacity": bool(item.get("capacity", False)),
                "capacity_increment": item.get("capacity_increment"),
            }
        )
    return output


def result_state_plan(analysis):
    """Build the ordered result-state index for an analysis."""
    states = {
        "initial": {"raw": "results-initial.txt", "json": "results-initial.json", "save": "initial.sav"},
    }
    stages = [stage for stage in analysis.stages if stage.kind != "initialization"]
    gravity = next((stage for stage in stages if stage.kind == "gravity"), None)
    if gravity is not None:
        states["gravity"] = {
            "raw": "results-gravity.txt",
            "json": "results-gravity.json",
            "save": "gravity.sav",
        }

    phases = [stage for stage in stages if stage.kind in ("loads", "displacements")]
    previous = "gravity" if gravity is not None else "initial"
    inherited_loads = []
    inherited_displacements = []
    for phase_index, stage in enumerate(phases):
        phase_name = stage.name
        prefix = phase_name.replace("loads", "load", 1).replace("displacements", "displacement", 1)
        is_last = phase_index == len(phases) - 1
        final_raw = "results-final.txt" if is_last else "results-{}-final.txt".format(prefix)
        final_json = "raw-results.json" if is_last else "results-{}-final.json".format(prefix)
        final_save = "{}-final.sav".format(prefix)

        if stage.kind == "loads":
            point_loads = list(stage.point_loads)
            surface_loads = list(stage.surface_loads)
            items = point_loads + surface_loads
            maximum_steps = max(int(item["steps"]) for item in items)
            if stage.options.get("save_steps", True):
                for step in range(1, maximum_steps + 1):
                    total = sum(
                        float(item.get("magnitude", item.get("face_area", 0.0) * sum(float(value) ** 2 for value in item.get("traction", [])) ** 0.5))
                        * min(step, int(item["steps"]))
                        / float(item["steps"])
                        for item in items
                    )
                    stem = "{}-step-{:04d}-{}N".format(prefix, step, int(round(total)))
                    states["{}-step-{:04d}".format(prefix, step)] = {
                        "raw": "results-{}.txt".format(stem),
                        "json": "results-{}.json".format(stem),
                        "save": "{}.sav".format(stem),
                        "step": step,
                        "source_state": previous,
                        "applied_loads": inherited_loads + applied_loads_at_step(items, step),
                        "prescribed_displacements": inherited_displacements,
                    }
            inherited_loads = inherited_loads + applied_loads_at_step(items, maximum_steps)
        else:
            items = list(stage.displacements)
            maximum_steps = max(int(item["steps"]) for item in items)
            if stage.options.get("save_steps", True):
                for step in range(1, maximum_steps + 1):
                    total = sum(float(item["magnitude"]) * min(step, int(item["steps"])) / float(item["steps"]) for item in items)
                    stem = "{}-step-{:04d}-{}um".format(prefix, step, int(round(total * 1e6)))
                    states["{}-step-{:04d}".format(prefix, step)] = {
                        "raw": "results-{}.txt".format(stem),
                        "json": "results-{}.json".format(stem),
                        "save": "{}.sav".format(stem),
                        "step": step,
                        "source_state": previous,
                        "applied_loads": inherited_loads,
                        "prescribed_displacements": inherited_displacements + prescribed_displacements_at_step(items, step),
                    }
            inherited_displacements = inherited_displacements + prescribed_displacements_at_step(items, maximum_steps)

        states[phase_name] = {
            "raw": final_raw,
            "json": final_json,
            "save": final_save,
            "step": maximum_steps,
            "source_state": previous,
            "applied_loads": inherited_loads,
            "prescribed_displacements": inherited_displacements,
        }
        previous = phase_name

    if phases:
        states["final"] = dict(states[previous])
        states["final"]["raw"] = "results-final.txt"
        states["final"]["json"] = "raw-results.json"
    else:
        states["final"] = {
            "raw": "results-final.txt",
            "json": "raw-results.json",
            "save": states[previous]["save"],
        }
    return states


def load_result_state(run_directory, state="final"):
    """Load an analysis and one named native result state from a run folder."""
    run_directory = Path(run_directory).resolve()
    manifest = json.loads((run_directory / "manifest.json").read_text(encoding="utf-8"))
    states = manifest.get("result_states", {})
    if not states:
        states = {
            "initial": {"raw": manifest["files"]["initial_results"], "json": "results-initial.json"},
            "final": {"raw": manifest["files"]["final_results"], "json": manifest["files"]["raw_results"]},
        }
        gravity_path = run_directory / "results-gravity.txt"
        if gravity_path.is_file():
            states["gravity"] = {"raw": gravity_path.name, "json": "results-gravity.json"}
    if state not in states:
        raise KeyError("Unknown result state {!r}. Available states: {}".format(state, ", ".join(states) or "none"))
    entry = states[state]
    analysis = compas.json_load(run_directory / manifest["files"]["analysis"])
    json_path = run_directory / entry["json"]
    raw_path = run_directory / entry["raw"]
    if raw_path.is_file():
        # Prefer the source log so legacy append-mode files are reduced to
        # their last snapshot by the current parser.
        results = parse_results_file(raw_path)
    elif json_path.is_file():
        results = compas.json_load(json_path)
    else:
        raise FileNotFoundError("Result state {!r} was not produced: {}".format(state, raw_path))
    results.metadata.update(
        result_state=state,
        result_step=entry.get("step"),
        applied_loads=list(entry.get("applied_loads", [])),
        prescribed_displacements=list(entry.get("prescribed_displacements", [])),
    )
    return analysis, results
