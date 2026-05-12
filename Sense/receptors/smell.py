import os
import re
import subprocess
from pathlib import Path


def smell_environment(target_directory: str) -> dict:
    """
    The Nose (Olfactory Receptor): Pure, zero-token static analysis.
    Transduces the physical state of the directory into raw data (chemicals).
    """
    scan_path = Path(target_directory).resolve()

    # Mypy safe typing
    data: dict[str, list[str]] = {
        "code_rot": [],
        "empty_files": [],
        "broken_links": [],
        "dead_media": [],
    }

    if not scan_path.exists() or not scan_path.is_dir():
        return {"error": "Target directory not found."}

    # 1. Chemical Sniff: Code Rot (via Ruff)
    try:
        ruff_result = subprocess.run(
            ["uv", "run", "ruff", "check", str(scan_path)],
            capture_output=True,
            text=True,
            shell=False,
        )
        if ruff_result.returncode != 0:
            clean_ruff = ruff_result.stdout.replace(str(scan_path) + os.sep, "")
            data["code_rot"] = clean_ruff.strip().split("\n")
    except Exception as e:
        data["code_rot"].append(f"Failed to run ruff: {str(e)}")

    # --- THE MUCUS MEMBRANE (Filter out digital noise) ---
    IGNORE_DIRS = {
        "System",
        "node_modules",
        "__pycache__",
        "venv",
        ".venv",
        "env",
        "dist",
        "build",
        "coverage",
    }

    # 2. Pre-compute graph for broken links (Safely!)
    all_md_files = set()
    for root, dirs, files in os.walk(scan_path):
        # Prune the walk in-place so it physically cannot enter ignored folders
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".md"):
                all_md_files.add(file)

    # 3. Semantic & Media Sniff
    for root, dirs, files in os.walk(scan_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]

        for file in files:
            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(scan_path)).replace("\\", "/")
            try:
                size = file_path.stat().st_size

                if (
                    file.endswith((".wav", ".mp3", ".png", ".jpg", ".pdf"))
                    and size == 0
                ):
                    data["dead_media"].append(rel_path)

                elif file.endswith(".md"):
                    if size < 20:
                        data["empty_files"].append(rel_path)
                    else:
                        content = file_path.read_text(errors="ignore")
                        links = re.findall(r"\[\[(.*?)\]\]", content)
                        for link in links:
                            target_name = link.split("|")[0] + ".md"
                            if target_name not in all_md_files:
                                data["broken_links"].append(
                                    f"{rel_path} -> Missing: [[{target_name}]]"
                                )
            except Exception:
                pass

    return data
