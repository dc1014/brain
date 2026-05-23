# --- System/tests/tools/test_epistemic.py ---
import json
from pathlib import Path
from System.tools.epistemic import extract_trajectory, native_ripgrep_search
from System.neuroanatomy.autonomic.autonomic import consolidate_historical_facts


def test_trajectory_chronological_extraction(tmp_path: Path, mocker) -> None:
    """Confirms that raw XML tags are correctly collected and ordered chronologically."""
    mocker.patch("System.tools.epistemic.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.epistemic.is_safe_path", return_value=True)

    prof_dir = tmp_path / "Professional"
    prof_dir.mkdir()

    company_note = prof_dir / "AcmeCorp.md"
    company_note.write_text(
        "# Venture Ledger\n"
        '<fact type="arr" value="2500000" date="2026-01-01" />\n'
        '<fact type="arr" value="1200000" date="2025-01-01" valid_until="2026-01-01" />\n',
        encoding="utf-8",
    )

    result = extract_trajectory("Professional", "AcmeCorp", "arr")
    assert result.success is True

    parsed_data = json.loads(result.output)
    assert len(parsed_data) == 2
    # Verify accurate chronological order (2025 sorted ahead of 2026)
    assert parsed_data[0]["date"] == "2025-01-01"
    assert parsed_data[0]["value"] == "1200000"
    assert parsed_data[1]["date"] == "2026-01-01"


def test_historical_fact_consolidation_supersession() -> None:
    """Verifies that old facts are bounded with valid_until ranges during consolidation updates."""
    raw_md = '# Timeline\n<fact type="mrr" value="5000" date="2026-01-01" />'

    processed_md = consolidate_historical_facts(
        file_content=raw_md,
        current_date="2026-05-19",
        fact_type="mrr",
        new_value="8000",
    )

    assert 'valid_until="2026-05-19"' in processed_md
    assert '<fact type="mrr" value="8000" date="2026-05-19" />' in processed_md


def test_global_text_search_routing(mocker) -> None:
    """Verifies the epistemic tool correctly routes queries to the ripgrep engine."""
    from System.tools.epistemic import global_text_search

    # ⚡ THE SHIFT-LEFT FIX: Patch the function where it is LOOKED UP and called now!
    mock_rg = mocker.patch("System.tools.epistemic.native_ripgrep_search")
    mock_rg.return_value = "Mocked Ripgrep Output"

    res = global_text_search("find_me")

    # Assertions will now pass flawlessly because the mock is firing correctly
    assert res == "Mocked Ripgrep Output"
    mock_rg.assert_called_once_with("find_me")


def test_native_ripgrep_search_success(mocker, tmp_path: Path) -> None:
    """Proves the ripgrep wrapper cleanly formats valid SIMD search results."""
    mocker.patch("System.tools.epistemic.ROOT_DIR", tmp_path)
    (tmp_path / "Studio").mkdir()

    # Mock 'rg' existing on the system
    mocker.patch("System.tools.epistemic.shutil.which", return_value="/usr/bin/rg")

    # Mock the subprocess execution
    mock_run = mocker.patch("System.tools.epistemic.subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Studio/app.py\n10: def secure_auth():\n"

    # Mock the sidecar DB connection so it returns an empty abstract list
    mock_conn = mocker.patch("System.tools.epistemic._get_conn")
    mock_conn.return_value.cursor.return_value.fetchall.return_value = []

    result = native_ripgrep_search("secure_auth")

    assert "RIPGREP NATIVE SEARCH RESULTS" in result
    assert "Studio/app.py" in result


def test_native_ripgrep_injects_semantic_sidecar(mocker, tmp_path: Path) -> None:
    """DEFCON PROOF: Verifies the Hybrid Sidecar seamlessly injects summaries to protect LLM context windows."""
    mocker.patch("System.tools.epistemic.ROOT_DIR", tmp_path)
    (tmp_path / "Studio").mkdir()

    mocker.patch("System.tools.epistemic.shutil.which", return_value="/usr/bin/rg")

    mock_run = mocker.patch("System.tools.epistemic.subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Studio/heavy_file.md\n10: Match here\n"

    # Mock the database returning a semantic sidecar summary for this file
    mock_conn = mocker.patch("System.tools.epistemic._get_conn")
    mock_conn.return_value.cursor.return_value.fetchall.return_value = [
        ("Studio/heavy_file.md", "This is a dense, low-entropy abstract.")
    ]

    result = native_ripgrep_search("Match here")

    assert "SEMANTIC FILE CONTEXT" in result
    assert (
        "[Studio/heavy_file.md SUMMARY]: This is a dense, low-entropy abstract."
        in result
    )
