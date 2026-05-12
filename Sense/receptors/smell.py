import os
import re
import hashlib
import subprocess
from pathlib import Path
from collections import defaultdict


def smell_environment(target_directory: str) -> dict:
    """
    The Nose: Pure, zero-token static analysis.
    Now sniffs for Code Rot, Toxins, Cognitive Stagnation, Duplicates, Orphans,
    Digital Dust, Git Conflicts, and Structural Bleed.
    """
    scan_path = Path(target_directory).resolve()

    data: dict[str, list[str]] = {
        "code_rot": [],
        "empty_files": [],
        "broken_links": [],
        "dead_media": [],
        "toxic_rot": [],
        "cognitive_rot": [],
        "duplicate_files": [],
        "orphaned_media": [],
        "digital_dust": [],  # NEW
        "git_conflict_rot": [],  # NEW
        "structural_rot": [],  # NEW
    }

    if not scan_path.exists() or not scan_path.is_dir():
        return {"error": "Target directory not found."}

    # 1. Code Rot
    try:
        ruff_result = subprocess.run(
            ["uv", "run", "ruff", "check", str(scan_path)],
            capture_output=True,
            text=True,
            shell=False,
        )
        if ruff_result.returncode != 0:
            data["code_rot"] = (
                ruff_result.stdout.replace(str(scan_path) + os.sep, "")
                .strip()
                .split("\n")
            )
    except Exception as e:
        data["code_rot"].append(f"Failed to run ruff: {str(e)}")

    # THE MUCUS MEMBRANE
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
        ".git",
        ".trash",
        "Meta",
    }

    # RECEPTORS
    SECRET_REGEX = re.compile(
        r"(sk-ant-api03-[a-zA-Z0-9\-_]{40,}|sk-[a-zA-Z0-9]{40,}|ghp_[a-zA-Z0-9]{36})"
    )
    TODO_REGEX = re.compile(r"(?i)(TODO|FIXME):")
    CONFLICT_REGEX = re.compile(r"<{7} HEAD|={7}|>{7} [a-zA-Z0-9]")  # NEW

    all_md_files = set()
    all_linked_targets = set()
    file_hashes = defaultdict(list)
    all_media_files = set()

    for root, dirs, files in os.walk(scan_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]

        for file in files:
            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(scan_path)).replace("\\", "/")

            try:
                size = file_path.stat().st_size

                # NEW: Digital Dust (Temporary / OS Junk)
                if file.endswith((".bak", ".tmp", ".swp")) or file in (
                    ".DS_Store",
                    "Thumbs.db",
                ):
                    data["digital_dust"].append(rel_path)
                    continue  # Dust has no useful content to hash or read

                # 2. Dead Media
                if size == 0:
                    if file.endswith(
                        (".wav", ".mp3", ".png", ".jpg", ".jpeg", ".pdf", ".gif")
                    ):
                        data["dead_media"].append(rel_path)
                    elif file.endswith(".md"):
                        data["empty_files"].append(rel_path)
                    continue

                # 3. Duplicate Clone Smells (Fast MD5 Hashing)
                hasher = hashlib.md5()
                with open(file_path, "rb") as f:
                    buf = f.read(65536)
                    while len(buf) > 0:
                        hasher.update(buf)
                        buf = f.read(65536)
                file_hashes[hasher.hexdigest()].append(rel_path)

                # Track Media for Orphans
                if file.endswith(
                    (".wav", ".mp3", ".png", ".jpg", ".jpeg", ".pdf", ".gif")
                ):
                    all_media_files.add(rel_path)

                # Track Markdown for Content Smells
                elif file.endswith(".md"):
                    all_md_files.add(file)

                    content = file_path.read_text(errors="ignore")

                    # NEW: Structural Bleed (Malformed YAML Frontmatter)
                    if content.startswith("---\n") and content.find("\n---\n") == -1:
                        data["structural_rot"].append(
                            f"{rel_path} -> Unclosed YAML frontmatter"
                        )

                    # NEW: Git Conflict Trauma
                    if CONFLICT_REGEX.search(content):
                        data["git_conflict_rot"].append(
                            f"{rel_path} -> Unresolved git merge conflict"
                        )

                    # Toxic Rot (Exposed API Keys)
                    if SECRET_REGEX.search(content):
                        data["toxic_rot"].append(
                            f"{rel_path} -> Exposed API/Secret Key detected!"
                        )

                    # Cognitive Stagnation (TODO overload)
                    todos = len(TODO_REGEX.findall(content))
                    if todos > 5:
                        data["cognitive_rot"].append(
                            f"{rel_path} -> {todos} unresolved TODOs/FIXMEs"
                        )

                    # Extract Links
                    links = re.findall(r"\[\[(.*?)\]\]", content)
                    for link in links:
                        target = link.split("|")[0]
                        all_linked_targets.add(target)

            except Exception:
                pass

    # Post-process Orphans
    for media in all_media_files:
        media_name = Path(media).name
        if media_name not in all_linked_targets and media not in all_linked_targets:
            data["orphaned_media"].append(media)

    # Post-process Duplicates
    for file_hash, paths in file_hashes.items():
        if len(paths) > 1:
            data["duplicate_files"].append(f"Identical clones: {', '.join(paths)}")

    # Second pass for accurate Broken Links
    for root, dirs, files in os.walk(scan_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(scan_path)).replace("\\", "/")
                try:
                    content = file_path.read_text(errors="ignore")
                    links = re.findall(r"\[\[(.*?)\]\]", content)
                    for link in links:
                        target = link.split("|")[0]
                        target_name = target if "." in target else target + ".md"
                        if (
                            target_name.endswith(".md")
                            and target_name not in all_md_files
                        ):
                            data["broken_links"].append(
                                f"{rel_path} -> Missing: [[{target_name}]]"
                            )
                except Exception:
                    pass

    return data
