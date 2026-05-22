# --- System/neuroanatomy/cortical/mirror_neurons/momentum_manager.py ---
import json
import time
import os
import threading
from pathlib import Path
from typing import Dict, Any, cast
from System.core.locks import BiologicalLock
from System.neuroanatomy.cortical.mirror_neurons.style_parser import CorticalStyleParser

_STYLE_MUTEX = threading.Lock()


class AllostaticMomentumManager:
    """Governs frequency tracking ledgers, exponential moving dampening, and global consensus crawling passes."""

    def __init__(self, style_path: Path, engram_path: Path, vault_path: str) -> None:
        self.style_path = style_path
        self.engram_path = engram_path
        self.vault_path = vault_path
        self.current_state: Dict[str, Any] = {}

    def analyze_and_mirror_style(self, sample_text: str, mode: str, mutex: Any) -> None:
        self.style_path.parent.mkdir(parents=True, exist_ok=True)

        fingerprint: Dict[str, Any] = {
            "code_conventions": {
                "indentation": "4-spaces",
                "naming": "snake_case",
                "docstrings": False,
            },
            "prose_cadence": {
                "bullet_style": "-",
                "nested_indentation": "4-spaces",
                "bold_preference": "asterisks",
                "italics_preference": "asterisks",
                "tone": "technical",
            },
            "allostatic_momentum": {},
        }

        with mutex:
            if self.style_path.exists():
                try:
                    with open(self.style_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, dict):
                            if "code_conventions" in loaded and isinstance(
                                loaded["code_conventions"], dict
                            ):
                                fingerprint["code_conventions"].update(
                                    loaded["code_conventions"]
                                )
                            if "prose_cadence" in loaded and isinstance(
                                loaded["prose_cadence"], dict
                            ):
                                fingerprint["prose_cadence"].update(
                                    loaded["prose_cadence"]
                                )
                            if "allostatic_momentum" in loaded and isinstance(
                                loaded["allostatic_momentum"], dict
                            ):
                                fingerprint["allostatic_momentum"].update(
                                    loaded["allostatic_momentum"]
                                )
                except Exception:
                    pass

        if "allostatic_momentum" not in fingerprint or not isinstance(
            fingerprint["allostatic_momentum"], dict
        ):
            fingerprint["allostatic_momentum"] = {}

        new_metrics = CorticalStyleParser.parse_metrics_isolated(sample_text, mode)
        keys_to_stabilize = []

        if mode == "code":
            keys_to_stabilize = [
                (
                    "indentation",
                    "code_conventions",
                    new_metrics["code_conventions"]["indentation"],
                ),
                (
                    "naming",
                    "code_conventions",
                    new_metrics["code_conventions"]["naming"],
                ),
                (
                    "docstrings",
                    "code_conventions",
                    new_metrics["code_conventions"]["docstrings"],
                ),
            ]
        elif mode == "prose":
            keys_to_stabilize = [
                (
                    "bullet_style",
                    "prose_cadence",
                    new_metrics["prose_cadence"]["bullet_style"],
                ),
                (
                    "nested_indentation",
                    "prose_cadence",
                    new_metrics["prose_cadence"]["nested_indentation"],
                ),
                (
                    "bold_preference",
                    "prose_cadence",
                    new_metrics["prose_cadence"]["bold_preference"],
                ),
                (
                    "italics_preference",
                    "prose_cadence",
                    new_metrics["prose_cadence"]["italics_preference"],
                ),
                ("tone", "prose_cadence", new_metrics["prose_cadence"]["tone"]),
            ]

        allostatic_mom = cast(Dict[str, Any], fingerprint["allostatic_momentum"])

        for key, group, observed_val in keys_to_stabilize:
            if key not in allostatic_mom or not isinstance(allostatic_mom[key], dict):
                allostatic_mom[key] = {}

            tallies = cast(Dict[str, float], allostatic_mom[key])
            for val_key in list(tallies.keys()):
                tallies[val_key] = round(tallies[val_key] * 0.7, 2)

            val_str = str(observed_val)
            tallies[val_str] = min(5.0, round(tallies.get(val_str, 0.0) + 1.5, 2))

            for val_key in list(tallies.keys()):
                if tallies[val_key] < 0.05:
                    tallies.pop(val_key, None)

            if tallies:
                winning_val_str = max(tallies, key=lambda k: tallies[k])
                group_dict = fingerprint.get(group)
                if isinstance(group_dict, dict):
                    if key == "docstrings":
                        group_dict[key] = winning_val_str == "True"
                    else:
                        group_dict[key] = winning_val_str

        for k in list(allostatic_mom.keys()):
            if not allostatic_mom[k]:
                allostatic_mom.pop(k, None)

        self.current_state = {
            "code_conventions": fingerprint.get("code_conventions", {}),
            "prose_cadence": fingerprint.get("prose_cadence", {}),
        }

        tmp_style_path = self.style_path.with_suffix(".tmp")
        with mutex:
            with BiologicalLock(str(self.style_path)):
                try:
                    with open(tmp_style_path, "w", encoding="utf-8") as f:
                        json.dump(fingerprint, f, indent=2)
                    os.replace(tmp_style_path, self.style_path)
                except Exception:
                    if tmp_style_path.exists():
                        try:
                            os.remove(tmp_style_path)
                        except OSError:
                            pass
                    pass

    def consolidate_stylistic_baseline(self, mutex: Any) -> None:
        """Crawls all workspace subdirectories to establish long-term structural engram footprints."""
        core_domains = ["Studio", "Personal", "Professional", "Meta"]
        ignore_parts = {".git", "__pycache__", ".venv", ".trash", "node_modules"}

        code_indent_counts: Dict[str, int] = {}
        code_naming_counts: Dict[str, int] = {}
        code_docstring_counts: Dict[bool, int] = {True: 0, False: 0}

        prose_bullet_counts: Dict[str, int] = {}
        prose_indent_counts: Dict[str, int] = {}
        prose_bold_counts: Dict[str, int] = {}
        prose_italics_counts: Dict[str, int] = {}
        prose_tone_counts: Dict[str, int] = {}

        for domain in core_domains:
            domain_path = Path(self.vault_path) / domain
            if not domain_path.exists():
                continue
            for root, dirs, files in os.walk(str(domain_path)):
                dirs[:] = [d for d in dirs if d not in ignore_parts]
                for file in files:
                    full_path = os.path.join(root, file).replace("\\", "/")
                    try:
                        if file.endswith(".py"):
                            content = Path(full_path).read_text(encoding="utf-8")
                            res = CorticalStyleParser.parse_metrics_isolated(
                                content, mode="code"
                            )
                            cc = res["code_conventions"]
                            code_indent_counts[cc["indentation"]] = (
                                code_indent_counts.get(cc["indentation"], 0) + 1
                            )
                            code_naming_counts[cc["naming"]] = (
                                code_naming_counts.get(cc["naming"], 0) + 1
                            )
                            code_docstring_counts[cc["docstrings"]] += 1
                        elif file.endswith(".md"):
                            content = Path(full_path).read_text(encoding="utf-8")
                            res = CorticalStyleParser.parse_metrics_isolated(
                                content, mode="prose"
                            )
                            pc = res["prose_cadence"]
                            prose_bullet_counts[pc["bullet_style"]] = (
                                prose_bullet_counts.get(pc["bullet_style"], 0) + 1
                            )
                            prose_indent_counts[pc["nested_indentation"]] = (
                                prose_indent_counts.get(pc["nested_indentation"], 0) + 1
                            )
                            prose_bold_counts[pc["bold_preference"]] = (
                                prose_bold_counts.get(pc["bold_preference"], 0) + 1
                            )
                            prose_italics_counts[pc["italics_preference"]] = (
                                prose_italics_counts.get(pc["italics_preference"], 0)
                                + 1
                            )
                            prose_tone_counts[pc["tone"]] = (
                                prose_tone_counts.get(pc["tone"], 0) + 1
                            )
                    except Exception:
                        pass

        fingerprint: Dict[str, Any] = {
            "code_conventions": {
                "indentation": "4-spaces",
                "naming": "snake_case",
                "docstrings": False,
            },
            "prose_cadence": {
                "bullet_style": "-",
                "nested_indentation": "4-spaces",
                "bold_preference": "asterisks",
                "italics_preference": "asterisks",
                "tone": "technical",
            },
            "allostatic_momentum": {},
        }

        if code_indent_counts:
            fingerprint["code_conventions"]["indentation"] = max(
                code_indent_counts, key=lambda k: code_indent_counts[k]
            )
        if code_naming_counts:
            fingerprint["code_conventions"]["naming"] = max(
                code_naming_counts, key=lambda k: code_naming_counts[k]
            )
        if sum(code_docstring_counts.values()) > 0:
            fingerprint["code_conventions"]["docstrings"] = (
                code_docstring_counts[True] >= code_docstring_counts[False]
            )

        if prose_bullet_counts:
            fingerprint["prose_cadence"]["bullet_style"] = max(
                prose_bullet_counts, key=lambda k: prose_bullet_counts[k]
            )
        if prose_indent_counts:
            fingerprint["prose_cadence"]["nested_indentation"] = max(
                prose_indent_counts, key=lambda k: prose_indent_counts[k]
            )
        if prose_bold_counts:
            fingerprint["prose_cadence"]["bold_preference"] = max(
                prose_bold_counts, key=lambda k: prose_bold_counts[k]
            )
        if prose_italics_counts:
            fingerprint["prose_cadence"]["italics_preference"] = max(
                prose_italics_counts, key=lambda k: prose_italics_counts[k]
            )
        if prose_tone_counts:
            fingerprint["prose_cadence"]["tone"] = max(
                prose_tone_counts, key=lambda k: prose_tone_counts[k]
            )

        self.style_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_style_path = self.style_path.with_suffix(".tmp")
        with mutex:
            with BiologicalLock(str(self.style_path)):
                try:
                    with open(tmp_style_path, "w", encoding="utf-8") as f:
                        json.dump(fingerprint, f, indent=2)
                    os.replace(tmp_style_path, self.style_path)
                except Exception:
                    pass

        long_term_payload: Dict[str, Any] = {
            "code_conventions": fingerprint.get("code_conventions", {}),
            "prose_cadence": fingerprint.get("prose_cadence", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.engram_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_engram_path = self.engram_path.with_suffix(".tmp")
        with mutex:
            with BiologicalLock(str(self.engram_path)):
                try:
                    with open(tmp_engram_path, "w", encoding="utf-8") as f:
                        json.dump(long_term_payload, f, indent=2)
                    os.replace(tmp_engram_path, self.engram_path)
                except Exception:
                    pass
