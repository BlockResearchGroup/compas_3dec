"""Discovery of locally installed 3DEC executables."""

import os
import re
import shutil
from pathlib import Path

ENVIRONMENT_VARIABLE = "COMPAS_3DEC_EXECUTABLE"


def _version_token(version):
    if version is None:
        return None
    parts = re.findall(r"\d+", str(version))
    return "".join(parts[:2]) if parts else None


def _matches_version(path, version):
    token = _version_token(version)
    if token is None:
        return True
    return any(part.startswith(token) for part in re.findall(r"\d+", str(path)))


def _default_itasca_roots():
    roots = []
    for variable in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
        program_files = os.environ.get(variable)
        if program_files:
            roots.append(Path(program_files) / "Itasca")
    if os.name == "nt":
        roots.append(Path(r"C:\Program Files\Itasca"))
    return roots


def _candidate_roots(search_roots):
    roots = _default_itasca_roots() if search_roots is None else [Path(path) for path in search_roots]
    unique = []
    seen = set()
    for root in roots:
        candidates = [root]
        if root.name.lower() != "itasca":
            candidates.append(root / "Itasca")
        for candidate in candidates:
            key = os.path.normcase(os.path.abspath(str(candidate)))
            if key not in seen:
                seen.add(key)
                unique.append(candidate)
    return unique


def _installed_candidates(search_roots):
    candidates = []
    for itasca_root in _candidate_roots(search_roots):
        if not itasca_root.is_dir():
            continue
        for product in itasca_root.glob("3DEC*"):
            if not product.is_dir():
                continue
            for path in product.rglob("*"):
                if not path.is_file():
                    continue
                name = path.name.lower()
                if re.fullmatch(r"3dec\d*(?:_console)?(?:\.exe)?", name):
                    candidates.append(path)
    return candidates


def _path_candidates(version):
    token = _version_token(version)
    names = ["3dec_console", "3dec"]
    if token:
        # Itasca commonly encodes 7.0 as 700 and 9.0 as 900.
        encoded = token + "0"
        names = ["3dec{}_console".format(encoded), "3dec{}".format(encoded)] + names
    if os.name == "nt":
        names = [name + ".exe" for name in names]
    return [Path(path) for name in names for path in [shutil.which(name)] if path]


def _candidate_score(path, version):
    name = path.name.lower()
    digits = re.findall(r"\d+", str(path))
    installed_version = int(digits[-1]) if digits else 0
    return (
        1 if _matches_version(path, version) else 0,
        1 if "console" in name else 0,
        installed_version,
        str(path).lower(),
    )


def find_3dec_executable(version=None, search_roots=None):
    """Find a locally installed 3DEC executable.

    Parameters
    ----------
    version : str, optional
        Requested 3DEC version, for example ``"7.0"`` or ``"9.0"``.
    search_roots : sequence of path-like, optional
        Installation roots to inspect instead of the platform defaults. Each
        path may be either an Itasca directory or its parent directory.

    Returns
    -------
    :class:`pathlib.Path` or None
        The preferred executable, or ``None`` if no matching installation is
        found.

    Notes
    -----
    ``COMPAS_3DEC_EXECUTABLE`` takes priority over automatic discovery.
    Automatic discovery checks ``PATH`` and then bounded ``Itasca/3DEC*``
    installation directories; it never searches an entire drive.
    """
    configured = os.environ.get(ENVIRONMENT_VARIABLE)
    if configured:
        path = Path(configured.strip().strip('"')).expanduser()
        if path.is_file():
            return path.resolve()

    candidates = _path_candidates(version) + _installed_candidates(search_roots)
    candidates = [path.resolve() for path in candidates if _matches_version(path, version)]
    if not candidates:
        return None
    return max(set(candidates), key=lambda path: _candidate_score(path, version))
