import pytest
from System.neuroanatomy.limbic.hippocampus import (
    _get_conn,
    _compute_hash,
    encode_memory,  # ⚡ Reverted to original name
    rebuild_index,
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
