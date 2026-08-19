from compas_3dec.solver import find_3dec_executable


def make_executable(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path.resolve()


def test_find_executable_below_itasca_folder(tmp_path, monkeypatch):
    monkeypatch.delenv("COMPAS_3DEC_EXECUTABLE", raising=False)
    executable = make_executable(tmp_path / "Itasca" / "3DEC700" / "exe64" / "3dec700_console.exe")

    found = find_3dec_executable(version="7.0", search_roots=[tmp_path])

    assert found == executable


def test_find_executable_selects_requested_version(tmp_path, monkeypatch):
    monkeypatch.delenv("COMPAS_3DEC_EXECUTABLE", raising=False)
    make_executable(tmp_path / "Itasca" / "3DEC700" / "exe64" / "3dec700_console.exe")
    executable_9 = make_executable(tmp_path / "Itasca" / "3DEC900" / "exe64" / "3dec900_console.exe")

    found = find_3dec_executable(version="9.0", search_roots=[tmp_path])

    assert found == executable_9


def test_find_executable_prefers_console_variant(tmp_path, monkeypatch):
    monkeypatch.delenv("COMPAS_3DEC_EXECUTABLE", raising=False)
    make_executable(tmp_path / "Itasca" / "3DEC700" / "exe64" / "3dec700.exe")
    console = make_executable(tmp_path / "Itasca" / "3DEC700" / "exe64" / "3dec700_console.exe")

    found = find_3dec_executable(version="7.0", search_roots=[tmp_path])

    assert found == console
