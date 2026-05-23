import pytest
from System.neuroanatomy.limbic.hippocampus import (
    _get_conn,
    _compute_hash,
    encode_memory,
    rebuild_index,
    native_ripgrep_search,  # ⚡ NEW: Import the search function so the tests can see it!
)


@pytest.fixture(autouse=True)
def clean_db(tmp_path, mocker):
    """Mocks the database path to a temp dir so we don't nuke the real Hippocampus."""
    test_db = tmp_path / "hippocampus_test.db"
    mocker.patch("System.neuroanatomy.limbic.hippocampus.DB_PATH", test_db)
    yield
    if test_db.exists():
        test_db.unlink()


def test_cas_hash_generation():
    """Proves the BLAKE3/SHA-256 equivalent hashing generates pure, deterministic boundaries."""
    content = "Hello, Brain OS!"
    hash1 = _compute_hash(content)
    hash2 = _compute_hash("Hello, Brain OS!")
    hash3 = _compute_hash("Hello, brain os!")

    assert hash1 == hash2
    assert hash1 != hash3


def test_encode_single_memory_cas_gatekeeper():
    """DEFCON PROOF: Verifies O(1) mutations are intercepted and aborted if the hash perfectly matches."""
    filepath = "Personal/test_note.md"
    content = "# My Local File"

    # 1. First encode should insert natively and return True
    result1 = encode_memory(filepath, content)
    assert result1 is True

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content_hash FROM file_hashes WHERE filepath = ?", (filepath,)
    )
    assert cursor.fetchone()[0] == _compute_hash(content)
    conn.close()

    # 2. Second encode with SAME content should hit the CAS gatekeeper and return False (Aborted)
    result2 = encode_memory(filepath, content)
    assert result2 is False

    # 3. Third encode with DIFFERENT content should surgically update the table and return True
    new_content = "# My Updated Local File"
    result3 = encode_memory(filepath, new_content)
    assert result3 is True

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content_hash FROM file_hashes WHERE filepath = ?", (filepath,)
    )
    assert cursor.fetchone()[0] == _compute_hash(new_content)
    conn.close()


def test_rebuild_index_incremental_sync_and_orphan_cleanup(tmp_path, mocker):
    """Proves that a full system index rebuild dynamically trims dead files while leaving untouched hashes completely alone."""
    mocker.patch("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)

    studio = tmp_path / "Studio"
    studio.mkdir()
    test_file = studio / "doc.md"
    test_file.write_text("Version 1.0", encoding="utf-8")

    # Pass 1: Initial rebuild caches the file
    rebuild_index()

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content_hash FROM file_hashes WHERE filepath = ?", ("Studio/doc.md",)
    )
    assert cursor.fetchone()[0] == _compute_hash("Version 1.0")
    conn.close()

    # Pass 2: Delete the physical file and verify the graph prunes the orphan natively
    test_file.unlink()
    rebuild_index()

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM file_hashes WHERE filepath = ?", ("Studio/doc.md",))
    assert cursor.fetchone() is None
    cursor.execute("SELECT * FROM memories WHERE filepath = ?", ("Studio/doc.md",))
    assert cursor.fetchone() is None
    conn.close()


def test_native_ripgrep_search_success(mocker, tmp_path):
    """Proves the ripgrep wrapper cleanly formats valid SIMD search results."""
    mocker.patch("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)
    (tmp_path / "Studio").mkdir()

    # Mock 'rg' existing on the system
    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.shutil.which",
        return_value="/usr/bin/rg",
    )

    # Mock the subprocess execution
    mock_run = mocker.patch("System.neuroanatomy.limbic.hippocampus.subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Studio/app.py\n10: def secure_auth():\n"

    result = native_ripgrep_search("secure_auth")

    assert "RIPGREP NATIVE SEARCH RESULTS" in result
    assert "Studio/app.py" in result
    assert mock_run.call_args[0][0][:8] == [
        "/usr/bin/rg",
        "-i",
        "-n",
        "--heading",
        "-m",
        "5",
        "-M",
        "150",
    ]


def test_native_ripgrep_search_missing_binary(mocker):
    """Proves the system degrades gracefully if ripgrep isn't installed."""
    # Force shutil.which to return None, simulating a missing binary
    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.shutil.which", return_value=None
    )

    result = native_ripgrep_search("query")
    assert "Ripgrep binary ('rg') not found" in result


def test_native_ripgrep_injects_semantic_sidecar(mocker, tmp_path):
    """DEFCON PROOF: Verifies the Hybrid Sidecar seamlessly injects summaries to protect LLM context windows."""
    mocker.patch("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)
    (tmp_path / "Studio").mkdir()

    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.shutil.which",
        return_value="/usr/bin/rg",
    )
    mock_run = mocker.patch("System.neuroanatomy.limbic.hippocampus.subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Studio/heavy_file.md\n10: Match here\n"

    # Seed the semantic sidecar manually
    conn = _get_conn()
    conn.execute(
        "INSERT INTO semantic_cache (filepath, summary, last_summarized) VALUES (?, ?, ?)",
        ("Studio/heavy_file.md", "This is a dense, low-entropy abstract.", 12345),
    )
    conn.commit()
    conn.close()

    # Trigger the search
    result = native_ripgrep_search("Match")

    # Assert the illusion was stitched correctly
    assert "SEMANTIC FILE CONTEXT" in result
    assert (
        "[Studio/heavy_file.md SUMMARY]: This is a dense, low-entropy abstract."
        in result
    )
