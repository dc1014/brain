import pytest
from System.tools.file_system import (
    write_safe_file,
    read_safe_file,
    list_safe_directory,
    rename_safe_file,
    append_safe_file,
    copy_safe_file,
    delete_safe_file,
    write_multiple_files,
)


@pytest.fixture
def mock_env(mocker, tmp_path):
    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.file_system.is_safe_path", return_value=True)
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.scan_for_pathogens",
        return_value=(True, ""),
    )
    mocker.patch("System.neuroanatomy.autonomic.vestibular.create_snapshot")
    return tmp_path


def test_write_safe_file(mock_env):
    res = write_safe_file("test.txt", "data")
    assert res.success is True
    assert (mock_env / "test.txt").read_text(encoding="utf-8") == "data"


def test_write_safe_file_blocked_adr(mock_env):
    res = write_safe_file("adr/test.md", "data")
    assert res.success is False
    assert "Cannot modify ADRs" in res.output


def test_write_safe_file_pathogen_blocked(mocker, mock_env):
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.scan_for_pathogens",
        return_value=(False, "Virus"),
    )
    res = write_safe_file("test.txt", "data")
    assert res.success is False
    assert "Virus" in res.output


def test_read_safe_file_success(mock_env):
    target = mock_env / "read.txt"
    target.write_text("info", encoding="utf-8")
    res = read_safe_file("read.txt")
    assert res.success is True
    assert "info" in res.output


def test_list_safe_directory(mock_env):
    target = mock_env / "dir"
    target.mkdir()
    (target / "file.txt").touch()
    res = list_safe_directory("dir")
    assert res.success is True
    assert "file.txt" in res.output


def test_rename_safe_file(mock_env):
    old = mock_env / "old.txt"
    old.write_text("data")
    res = rename_safe_file("old.txt", "new.txt")
    assert res.success is True
    assert (mock_env / "new.txt").exists()


def test_append_safe_file(mock_env):
    target = mock_env / "app.txt"
    target.write_text("line1")
    res = append_safe_file("app.txt", "line2")
    assert res.success is True
    assert "line2" in target.read_text()


def test_copy_safe_file(mock_env):
    src = mock_env / "src.txt"
    src.write_text("copy")
    res = copy_safe_file("src.txt", "dest.txt")
    assert res.success is True
    assert (mock_env / "dest.txt").exists()


def test_delete_safe_file(mock_env):
    target = mock_env / "del.txt"
    target.write_text("trash")
    res = delete_safe_file("del.txt")
    assert res.success is True
    assert not target.exists()


def test_write_multiple_files(mock_env):
    res = write_multiple_files(
        [{"filepath": "1.txt", "content": "1"}, {"filepath": "2.txt", "content": "2"}]
    )
    assert "Successfully wrote: 1.txt" in res
    assert (mock_env / "1.txt").exists()
