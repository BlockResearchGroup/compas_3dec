import os
import subprocess
from pathlib import Path
from time import perf_counter

import compas
from compas_3dec.analysis import ThreeDECAnalysis

from .commands import render_analysis_deck
from .commands import render_displacement_deck
from .commands import render_geometry
from .commands import render_load_deck
from .discovery import find_3dec_executable
from .fish import fish_dialect
from .io import ThreeDECWorkspace
from .io import bind_initial_gridpoints
from .io import parse_results_file
from .stages import ThreeDECStagePlan
from .states import result_state_plan


class ThreeDECSolver:
    """Runtime orchestration for a 3DEC analysis.

    Paths and executable configuration deliberately live here rather than in
    the serializable :class:`ThreeDECAnalysis`.
    """

    def __init__(
        self,
        version="7.0",
        executable=None,
        workspace=None,
        arguments=None,
        suppress_output=True,
        timeout=None,
        gridpoint_tolerance=1e-6,
    ):
        self.version = str(version)
        self.executable = executable
        self.workspace = workspace
        self.arguments = list(arguments or [])
        self.suppress_output = bool(suppress_output)
        self.timeout = timeout
        self.gridpoint_tolerance = float(gridpoint_tolerance)
        self.fish = fish_dialect(self.version)

    def create_results(self, analysis, raw_results):
        """Convert native records into ``compas_dem.Results`` explicitly."""
        return raw_results.to_compas_dem_results(analysis)

    def prepare(self, problem):
        """Convert a ``compas_dem`` problem into a portable 3DEC analysis.

        This method is the solver-adapter entry point used by ``compas_dem``.
        It does not create a run directory or write 3DEC input files; that
        happens later in :meth:`prepare_run` when :meth:`solve` is called.
        """
        from compas_3dec.analysis import ThreeDECAnalysisBuilder

        return ThreeDECAnalysisBuilder.from_dem_problem(problem).build()

    def prepare_run(self, analysis, run_id=None):
        """Create an isolated dry-run workspace and all solver input files."""
        if not isinstance(analysis, ThreeDECAnalysis):
            raise TypeError("prepare_run expects a ThreeDECAnalysis.")

        stage_plan = ThreeDECStagePlan.from_analysis(analysis)
        workspace = ThreeDECWorkspace.create(
            root=self.workspace,
            run_id=run_id,
            analysis_name=analysis.name,
        )
        geometry_filename = "geometry.dat"
        deck_filename = "analysis.dat"
        initial_results_filename = "results-initial.txt"
        final_results_filename = "results-final.txt"
        gravity_results_filename = "results-gravity.txt"

        workspace.write_analysis(analysis)
        compas.json_dump(
            stage_plan,
            workspace.file("stages.json"),
            pretty=True,
        )
        workspace.write_text(
            geometry_filename,
            render_geometry(analysis),
        )
        workspace.write_text(
            deck_filename,
            render_analysis_deck(
                analysis=analysis,
                stage_plan=stage_plan,
                fish_dialect=self.fish,
                geometry_filename=geometry_filename,
                initial_results_filename=initial_results_filename,
                gravity_results_filename=gravity_results_filename,
                final_results_filename=final_results_filename,
            ),
        )
        state_plan = result_state_plan(analysis)
        phases = [stage for stage in stage_plan.stages if stage.kind in ("loads", "displacements")]
        stage_decks = []
        previous_state = "gravity"
        kind_counts = {"loads": 0, "displacements": 0}
        for index, stage in enumerate(phases):
            kind_counts[stage.kind] += 1
            count = kind_counts[stage.kind]
            base = "loads" if stage.kind == "loads" else "displacements"
            filename = "{}.dat".format(base) if count == 1 else "{}-{}.dat".format(base, count)
            prefix = stage.name.replace("loads", "load", 1).replace("displacements", "displacement", 1)
            final_results = state_plan[stage.name]["raw"]
            final_save = state_plan[stage.name]["save"]
            if stage.kind == "loads":
                text = render_load_deck(
                    analysis=analysis,
                    stage_plan=stage_plan,
                    fish_dialect=self.fish,
                    final_results_filename=final_results,
                    stage=stage,
                    restore_filename=state_plan[previous_state]["save"],
                    final_save_filename=final_save,
                    file_prefix=prefix,
                )
            else:
                text = render_displacement_deck(
                    analysis=analysis,
                    stage_plan=stage_plan,
                    fish_dialect=self.fish,
                    restore_filename=state_plan[previous_state]["save"],
                    final_results_filename=final_results,
                    stage=stage,
                    final_save_filename=final_save,
                    file_prefix=prefix,
                )
            workspace.write_text(filename, text)
            stage_decks.append(filename)
            previous_state = stage.name
        files = {
            "analysis": "analysis.json",
            "stages": "stages.json",
            "geometry": geometry_filename,
            "deck": deck_filename,
            "initial_results": initial_results_filename,
            "final_results": final_results_filename,
            "gravity_results": gravity_results_filename,
            "raw_results": "raw-results.json",
        }
        if any(stage.kind == "loads" for stage in phases):
            files["load_deck"] = "loads.dat"
        if any(stage.kind == "displacements" for stage in phases):
            files["displacement_deck"] = "displacements.dat"
        if stage_decks:
            files["stage_decks"] = stage_decks
        workspace.initialise_manifest(
            analysis=analysis,
            version=self.version,
            files=files,
        )
        workspace.update_manifest(result_states=state_plan)
        return workspace

    def report_solve_summary(self, raw_results, elapsed_seconds=None):
        """Print the elapsed time, solve ratio, and equilibrium status.

        Parameters
        ----------
        raw_results : :class:`ThreeDECRawResults`
            Native results returned by 3DEC.
        elapsed_seconds : float, optional
            Total elapsed time of the solver workflow. If omitted, the value
            stored in the result metadata is used.

        Returns
        -------
        bool or None
            Whether equilibrium was reached, or ``None`` when no solve ratio
            was exported by 3DEC.
        """
        # 3DEC can leave the Windows console cursor on a carriage-returned
        # progress line. Start and finish the Python summary on clean lines so
        # the shell prompt cannot overwrite or be appended to its last entry.
        print()
        metadata = raw_results.metadata
        elapsed = elapsed_seconds if elapsed_seconds is not None else metadata.get("elapsed_seconds")
        if elapsed is not None:
            print("3DEC execution time = {:.3f} seconds".format(float(elapsed)))

        ratio = metadata.get("ratio_local")
        if ratio is None:
            print("Solve ratio was not exported by 3DEC")
            print(flush=True)
            return None

        converged = metadata.get("converged")
        if converged is True:
            print("Equilibrium reached")
        elif converged is False:
            print("Equilibrium NOT reached")
        else:
            print("Equilibrium status unavailable")
        print("Solve ratio = {}".format(ratio))

        target = metadata.get("target_ratio")
        if target is not None:
            print("Target solve ratio = {}".format(target))
        print(flush=True)
        return converged

    def solve(self, analysis, run_id=None):
        """Run a prepared analysis and return native ``ThreeDECRawResults``.

        The 3DEC executable is launched without a shell. The generated data
        file is passed as its final command-line argument, matching the legacy
        invocation used by this repository.
        """
        started_at = perf_counter()
        selected_executable = self.executable or find_3dec_executable(self.version)
        if not selected_executable:
            raise ValueError(
                "No 3DEC {} executable was found. Install 3DEC under the "
                "Itasca directory, set COMPAS_3DEC_EXECUTABLE, or pass "
                "executable=... to ThreeDECSolver. Use prepare_run() to "
                "generate files without launching 3DEC.".format(self.version)
            )

        executable = Path(str(selected_executable).strip('"')).resolve()
        if not executable.is_file():
            raise FileNotFoundError("The 3DEC executable does not exist: {}".format(executable))

        workspace = self.prepare_run(analysis, run_id=run_id)
        manifest = workspace.read_manifest()
        deck_names = [manifest["files"]["deck"]]
        stage_decks = manifest["files"].get("stage_decks")
        if stage_decks:
            deck_names.extend(stage_decks)
        else:
            if manifest["files"].get("load_deck"):
                deck_names.append(manifest["files"]["load_deck"])
            if manifest["files"].get("displacement_deck"):
                deck_names.append(manifest["files"]["displacement_deck"])
        commands = [[str(executable)] + self.arguments + [deck_name] for deck_name in deck_names]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        workspace.update_manifest(status="running", commands=commands)
        completed = None
        for command in commands:
            remaining_timeout = None
            if self.timeout is not None:
                remaining_timeout = max(
                    1e-6,
                    float(self.timeout) - (perf_counter() - started_at),
                )
            completed = subprocess.run(
                command,
                cwd=str(workspace.path),
                stdout=subprocess.DEVNULL if self.suppress_output else None,
                stderr=subprocess.DEVNULL if self.suppress_output else None,
                creationflags=creationflags,
                timeout=remaining_timeout,
                check=False,
            )
            if completed.returncode != 0:
                workspace.update_manifest(
                    status="failed",
                    returncode=completed.returncode,
                    failed_command=command,
                )
                raise RuntimeError(
                    "3DEC exited with return code {} while running {}. Run workspace: {}".format(
                        completed.returncode,
                        command[-1],
                        workspace.path,
                    )
                )

        initial_path = workspace.file(manifest["files"]["initial_results"])
        final_path = workspace.file(manifest["files"]["final_results"])
        missing = [str(path.name) for path in (initial_path, final_path) if not path.is_file()]
        if missing:
            workspace.update_manifest(
                status="failed",
                returncode=completed.returncode,
                missing_files=missing,
            )
            raise FileNotFoundError(
                "3DEC completed but did not create {} in {}.".format(
                    ", ".join(missing),
                    workspace.path,
                )
            )

        initial = parse_results_file(initial_path)
        bind_initial_gridpoints(
            analysis,
            initial,
            tolerance=self.gridpoint_tolerance,
        )
        final = parse_results_file(final_path)
        final.metadata.update(
            {
                "solver": "3DEC",
                "solver_version": self.version,
                "run_id": workspace.run_id,
                "returncode": completed.returncode,
                "analysis_id": str(analysis.guid),
                "model_id": analysis.model_id,
                "problem_id": analysis.problem_id,
            }
        )

        stage_plan = ThreeDECStagePlan.from_analysis(analysis)
        equilibrium_stage = stage_plan.stage("displacements") or stage_plan.stage("loads") or stage_plan.stage("gravity")
        if equilibrium_stage is not None and final.metadata.get("ratio_local") is not None:
            target = float(equilibrium_stage.options.get("ratio", 1e-5))
            final.metadata["target_ratio"] = target
            final.metadata["converged"] = float(final.metadata["ratio_local"]) <= target

        displacement_stage = stage_plan.stage("displacements")
        load_stage = stage_plan.stage("loads")
        capacity_kind = None
        if displacement_stage is not None and any(item.get("capacity") for item in displacement_stage.displacements or []):
            capacity_kind = "displacement"
        elif load_stage is not None and any(item.get("capacity") for item in list(load_stage.point_loads or []) + list(load_stage.surface_loads or [])):
            capacity_kind = "load"

        if capacity_kind is not None:
            prefix = "{}-step-".format(capacity_kind)
            produced = [(name, entry) for name, entry in manifest.get("result_states", {}).items() if name.startswith(prefix) and workspace.file(entry["raw"]).is_file()]
            if produced:
                _, actual = max(produced, key=lambda pair: int(pair[1].get("step", 0)))
                final_entry = manifest["result_states"]["final"]
                final_entry["step"] = actual["step"]
                for key in ("applied_loads", "prescribed_displacements", "source_state"):
                    if key in actual:
                        final_entry[key] = actual[key]
                converged = final.metadata.get("converged")
                final.metadata.update(
                    capacity_run=True,
                    capacity_kind=capacity_kind,
                    capacity_step=int(actual["step"]),
                    capacity_reached=converged is False,
                    last_converged_step=(max(int(actual["step"]) - 1, 0) if converged is False else int(actual["step"])),
                )
                workspace.update_manifest(result_states=manifest["result_states"])

        # Persist every produced state as portable COMPAS data. States not
        # reached because of early non-convergence remain indexed but absent.
        for state_name, state in manifest.get("result_states", {}).items():
            raw_path = workspace.file(state["raw"])
            if not raw_path.is_file():
                continue
            state_results = final if state_name == "final" else parse_results_file(raw_path)
            state_results.metadata.update(
                result_state=state_name,
                result_step=state.get("step"),
                applied_loads=list(state.get("applied_loads", [])),
                prescribed_displacements=list(state.get("prescribed_displacements", [])),
            )
            compas.json_dump(
                state_results,
                workspace.file(state["json"]),
                pretty=True,
            )

        contact_edges = set()
        for contact in final.contacts:
            edge = analysis.entity_map.bind_contact(
                contact["region_a"],
                contact["region_b"],
                contact["contact_id"],
            )
            contact_edges.add(edge)
        final.metadata.update(
            {
                "contact_topology_source": "3DEC",
                "contact_edge_count": len(contact_edges),
                "contact_count": len(final.contacts),
            }
        )

        elapsed_seconds = perf_counter() - started_at
        final.metadata["elapsed_seconds"] = elapsed_seconds

        # Persist gridpoint IDs and 3DEC-discovered contact topology in the
        # portable analysis snapshot without requiring compas_dem conversion.
        workspace.write_analysis(analysis)
        compas.json_dump(
            final,
            workspace.file(manifest["files"]["raw_results"]),
            pretty=True,
        )
        workspace.update_manifest(
            status="complete",
            returncode=completed.returncode,
            elapsed_seconds=elapsed_seconds,
            converged=final.metadata.get("converged"),
            contact_edge_count=final.metadata.get("contact_edge_count", 0),
            contact_count=final.metadata.get("contact_count", 0),
        )
        self.report_solve_summary(final, elapsed_seconds=elapsed_seconds)
        return final

    def solve_compas_dem(self, analysis, run_id=None):
        """Run 3DEC and explicitly convert the native output to DEM results."""
        raw_results = self.solve(analysis, run_id=run_id)
        return raw_results.to_compas_dem_results(analysis)
