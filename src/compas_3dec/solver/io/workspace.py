import json
import re
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path

import compas


class ThreeDECWorkspace:
    """Filesystem boundary for one isolated 3DEC run."""

    MANIFEST_SCHEMA_VERSION = 1

    def __init__(self, path, run_id=None):
        self.path = Path(path).resolve()
        self.run_id = str(run_id or self.path.name)

    @classmethod
    def create(cls, root=None, run_id=None, analysis_name=None):
        generated_run_id = run_id is None
        if run_id is None:
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(analysis_name or "analysis"))
            name = name.strip("._-") or "analysis"
            run_id = "{}_{}".format(
                name,
                datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

        if root is None:
            path = Path(tempfile.mkdtemp(prefix="compas_3dec-{}-".format(run_id)))
            return cls(path=path, run_id=path.name)

        root = Path(root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        run_id = str(run_id)
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
        return self.path / "manifest.json"

    def file(self, relative_path):
        path = (self.path / relative_path).resolve()
        if self.path != path and self.path not in path.parents:
            raise ValueError("Workspace paths must remain inside the run directory.")
        return path

    def write_text(self, relative_path, content):
        path = self.file(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(str(content))
        return path

    def write_analysis(self, analysis, relative_path="analysis.json"):
        path = self.file(relative_path)
        compas.json_dump(analysis, path, pretty=True)
        return path

    def initialise_manifest(self, analysis, version, files):
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
        manifest = self.read_manifest()
        manifest.update(updates)
        self._write_manifest(manifest)
        return manifest

    def read_manifest(self):
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest):
        with self.manifest_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(manifest, indent=2, sort_keys=True))
