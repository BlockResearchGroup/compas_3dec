import json
import re
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path

import compas


def _validate_run_id(run_id):
    """Return a safe single-directory run identifier."""
    run_id = str(run_id)
    if not run_id or run_id in (".", "..") or re.search(r"[\\/:*?\"<>|\x00-\x1f]", run_id):
        raise ValueError("run_id must be a non-empty directory name without path separators or reserved characters.")
    return run_id


class ThreeDECWorkspace:
    """Filesystem boundary for one isolated 3DEC run."""

    MANIFEST_SCHEMA_VERSION = 1

    def __init__(self, path, run_id=None):
        self.path = Path(path).resolve()
        self.run_id = str(run_id or self.path.name)

    @classmethod
    def create(cls, root=None, run_id=None, analysis_name=None):
        """Create a unique run directory.

        Parameters
        ----------
        root : path-like, optional
            Parent directory. A temporary directory is used when omitted.
        run_id : str, optional
            Explicit single-directory identifier. Path components are rejected.
        analysis_name : str, optional
            Prefix used for an automatically generated identifier.

        Returns
        -------
        :class:`ThreeDECWorkspace`
            The created workspace.
        """
        generated_run_id = run_id is None
        if run_id is None:
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(analysis_name or "analysis"))
            name = name.strip("._-") or "analysis"
            run_id = "{}_{}".format(
                name,
                datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

        run_id = _validate_run_id(run_id)

        if root is None:
            path = Path(tempfile.mkdtemp(prefix="compas_3dec-{}-".format(run_id)))
            return cls(path=path, run_id=path.name)

        root = Path(root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        candidate = run_id
        suffix = 2
        while True:
            path = root / candidate
            try:
                path.mkdir(parents=False, exist_ok=False)
                break
            except FileExistsError:
                if not generated_run_id:
                    raise
                candidate = "{}_{}".format(run_id, suffix)
                suffix += 1
        return cls(path=path, run_id=candidate)

    @property
    def manifest_path(self):
        """Path to the JSON run manifest."""
        return self.path / "manifest.json"

    def file(self, relative_path):
        """Resolve a path relative to this workspace without allowing escape."""
        path = (self.path / relative_path).resolve()
        if self.path != path and self.path not in path.parents:
            raise ValueError("Workspace paths must remain inside the run directory.")
        return path

    def write_text(self, relative_path, content):
        """Write UTF-8 text inside the workspace."""
        path = self.file(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(str(content))
        return path

    def write_analysis(self, analysis, relative_path="analysis.json"):
        """Serialise an analysis inside the workspace."""
        path = self.file(relative_path)
        compas.json_dump(analysis, path, pretty=True)
        return path

    def initialise_manifest(self, analysis, version, files):
        """Create and return the initial run manifest."""
        manifest = {
            "schema_version": self.MANIFEST_SCHEMA_VERSION,
            "run_id": self.run_id,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "status": "prepared",
            "solver": "3DEC",
            "solver_version": str(version),
            "analysis_id": str(analysis.guid),
            "model_id": analysis.model_id,
            "problem_id": analysis.problem_id,
            "files": dict(files),
        }
        self._write_manifest(manifest)
        return manifest

    def update_manifest(self, **updates):
        """Update and return the run manifest."""
        manifest = self.read_manifest()
        manifest.update(updates)
        self._write_manifest(manifest)
        return manifest

    def read_manifest(self):
        """Read the run manifest."""
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest):
        with self.manifest_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(manifest, indent=2, sort_keys=True))
