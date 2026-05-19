import os
import pytest
import System.tools.sandbox as sandbox_module
from System.tools.sandbox import is_safe_path, _is_windows_junction


def test_is_windows_junction_mocked(mocker, tmp_path):
    """
    Zero-Debt: Proves the Windows Junction detection logic works across platforms
    by mocking the ctypes kernel response. Ensures 100% branch coverage.
    """
    # 1. Test non-Windows / non-dir bypass
    test_file = tmp_path / "test.txt"
    test_file.touch()
    assert _is_windows_junction(test_file) is False

    # 2. Mock Windows environment and ctypes for an active junction
    mocker.patch("os.name", "nt")
    mock_ctypes = mocker.MagicMock()
    # 0x400 represents FILE_ATTRIBUTE_REPARSE_POINT (Junction/Symlink on Windows)
    mock_ctypes.windll.kernel32.GetFileAttributesW.return_value = 0x400
    mocker.patch.dict("sys.modules", {"ctypes": mock_ctypes})

    test_dir = tmp_path / "fake_junction"
    test_dir.mkdir()

    # Validation: The detector must flag this directory as a junction
    assert _is_windows_junction(test_dir) is True


def test_sandbox_rejects_symlink_parent_chain(mocker, tmp_path):
    """
    Zero-Debt: Proves that a symlink hidden anywhere in the parent directory
    chain is violently rejected by the sandbox before file access occurs.
    """
    mocker.patch.object(sandbox_module, "ROOT_DIR", tmp_path)
    mocker.patch.object(sandbox_module, "ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()

    # Create a malicious external target outside the allowed zones
    external_dir = tmp_path / "Windows_System32_Mock"
    external_dir.mkdir()
    (external_dir / "sam.txt").touch()

    # Create a deceptive symlink INSIDE Studio pointing OUTSIDE
    symlink_dir = studio_dir / "innocent_folder"
    try:
        os.symlink(external_dir, symlink_dir, target_is_directory=True)
    except OSError:
        pytest.skip(
            "Symlink creation requires elevated privileges/Developer Mode on this host."
        )

    # Attempt to access the file THROUGH the deceptive symlink
    sneaky_path = symlink_dir / "sam.txt"

    # Strict Validation: The sandbox must walk the parents, find the link, and reject it!
    assert is_safe_path(sneaky_path) is False


def test_sandbox_rejects_junction_parent_chain(mocker, tmp_path):
    """
    Zero-Debt: Proves that a Windows Junction hidden in the parent chain
    is caught and rejected, blocking the NTFS vulnerability.
    """
    mocker.patch.object(sandbox_module, "ROOT_DIR", tmp_path)
    mocker.patch.object(sandbox_module, "ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()
    junction_dir = studio_dir / "fake_junction"
    junction_dir.mkdir()
    target_file = junction_dir / "file.txt"
    target_file.touch()

    # Force the junction detector to return True for this specific folder to simulate an NTFS junction
    original_junction_check = sandbox_module._is_windows_junction

    def mock_junction_check(path):
        if path == junction_dir:
            return True
        return original_junction_check(path)

    mocker.patch.object(
        sandbox_module, "_is_windows_junction", side_effect=mock_junction_check
    )

    # Strict Validation: The sandbox must reject access to the file inside the junction
    assert is_safe_path(target_file) is False
