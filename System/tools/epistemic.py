# --- System/tools/epistemic.py ---
import os
import re
import datetime
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path
from System.core.schemas import ExecutionResult


def extract_trajectory(
    directory_path: str, entity_slug: str, fact_type: str
) -> ExecutionResult:
    """Tool entry point: Scans a file and chunks historical trajectories chronologically.

    Args:
        directory_path: Base workspace directory (e.g., 'Professional').
        entity_slug: Note document path modifier relative to directory root (e.g., 'AcmeCorp').
        fact_type: Target metric attribute string to track (e.g., 'arr').
    """
    target_dir = (ROOT_DIR / directory_path).resolve()
    if not is_safe_path(target_dir):
        reason = "SECURITY BLOCK: Cannot evaluate timeline data targets outside sandbox bounds."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    file_path = os.path.join(str(target_dir), f"{entity_slug}.md")
    if not os.path.exists(file_path):
        return ExecutionResult(
            success=False, output=f"Entity document target '{entity_slug}' not found."
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        reason = f"ERROR: Unreadable target node layout stream: {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    # Locate raw <fact> structures via regex safety passes
    fact_tags = re.findall(r"<fact[^>]*>", content)
    trajectory: List[Dict[str, str]] = []

    for tag in fact_tags:
        try:
            # Append self-closing marker to handle unclosed variants gracefully
            normalized_xml = tag if tag.endswith("/>") else tag.rstrip(">") + " />"
            root = ET.fromstring(normalized_xml)
            if root.get("type") == fact_type:
                trajectory.append(
                    {
                        "value": str(root.get("value")),
                        "date": str(root.get("date")),
                        "valid_until": str(root.get("valid_until", "PRESENT")),
                    }
                )
        except Exception:
            continue

    # Sort chronological results sequentially by date ascending
    trajectory.sort(key=lambda x: x["date"])

    output_str = json_dump_fallback(trajectory)
    return ExecutionResult(success=True, output=output_str)


def verify_trajectory_freshness(
    trajectory: List[Dict[str, str]], current_date_str: str
) -> Dict[str, Any]:
    """Inspects chronological entries to catch out-of-date parameters before execution loops.

    Args:
        trajectory: Chronological list of parsed fact dictionary configurations.
        current_date_str: Target reference date validation marker (e.g., '2026-05-19').

    Returns:
        A dictionary specifying if epistemic drift or factual decay was detected.
    """
    if not trajectory:
        return {"status": "EMPTY", "drift_detected": False}

    latest_fact = trajectory[-1]
    valid_until = latest_fact.get("valid_until", "PRESENT")

    if valid_until != "PRESENT":
        try:
            expiry_date = datetime.datetime.strptime(valid_until, "%Y-%m-%d")
            current_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d")

            if current_date > expiry_date:
                # Signal an active epistemic drift condition back up to the executive core
                return {
                    "status": "STALE",
                    "drift_detected": True,
                    "expired_metric": latest_fact.get("value"),
                }
        except ValueError:
            # Fall back to safe warning if string mapping is unparseable
            return {"status": "MALFORMED_BOUNDS", "drift_detected": True}

    return {"status": "FRESH", "drift_detected": False}


def json_dump_fallback(data: List[Dict[str, str]]) -> str:
    """Safely handles text formatting representation outputs without complex imports."""
    import json

    return json.dumps(trajectory_data_format(data), indent=2)


def trajectory_data_format(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return data


def global_text_search(query: str) -> str:
    """
    Executes a blazing-fast global regex search across the entire knowledge vault.
    Use this to find exact string matches, variable names, or phrases across all files.
    """
    from System.neuroanatomy.limbic.hippocampus import native_ripgrep_search

    return native_ripgrep_search(query)
