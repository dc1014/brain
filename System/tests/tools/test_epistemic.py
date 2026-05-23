# --- System/tests/tools/test_epistemic.py ---
import json
from pathlib import Path
from System.tools.epistemic import extract_trajectory
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


def test_global_text_search_routing(mocker):
    """Verifies the epistemic tool correctly routes queries to the ripgrep engine."""
    from System.tools.epistemic import global_text_search

    mock_rg = mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.native_ripgrep_search"
    )
    mock_rg.return_value = "Mocked Ripgrep Output"

    res = global_text_search("find_me")
    assert res == "Mocked Ripgrep Output"
    mock_rg.assert_called_once_with("find_me")
