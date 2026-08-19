#! python3
# venv: himass2

from pathlib import Path

from compas_3dec.rhino import draw_results
from compas_3dec.solver import load_result_state


HERE = Path(__file__).parent
RUNS = HERE / "runs"
RESULT_STATE = "final"  # e.g. "gravity" or "load-step-0005"

RUN_DIRECTORY = max(
    (path for path in RUNS.iterdir() if path.is_dir() and (path / "manifest.json").is_file()),
    key=lambda path: path.stat().st_mtime,
)

analysis, raw_results = load_result_state(RUN_DIRECTORY, state=RESULT_STATE)
postprocessed = raw_results.postprocess(analysis)

gravity_postprocessed = None
if RESULT_STATE != "gravity":
    _, gravity_results = load_result_state(RUN_DIRECTORY, state="gravity")
    gravity_postprocessed = gravity_results.postprocess(analysis)

draw_results(
    analysis,
    raw_results,
    postprocessed=postprocessed,
    gravity_postprocessed=gravity_postprocessed,
    clear_existing=True,
)
