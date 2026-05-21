# --- System/neuroanatomy/cortical/mirror_neurons.py ---
import json
import time
import os
import io
import tokenize
import re
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, cast
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock

console = Console()

# Global memory barrier to guard cross-thread fingerprint mutations deterministically
_STYLE_MUTEX = threading.Lock()


class MirrorNeurons:
    """Cortical Mirror Neurons Subsystem.

    Responsible for observing execution timelines of concurrent agents,
    tracking successful tool configurations, and extracting developer-specific
    coding styles and prose patterns using strict tokenization streams and multi-tier
    markdown block parsing with allostatic momentum bounds to eliminate style drift.
    """

    def __init__(self, observation_vault: Optional[str] = None) -> None:
        self.vault_path = observation_vault or str(ROOT_DIR)
        sanitized_vault = str(Path(self.vault_path)).replace("\\", "/")
        self.log_path = Path(sanitized_vault) / "Meta" / "mirror_observations.jsonl"
        self.style_path = (
            Path(sanitized_vault) / "System" / "config" / "stylistic_fingerprint.json"
        )
        self.engram_path = (
            Path(sanitized_vault) / "System" / "config" / "long_term_engram.json"
        )
        # O(1) Synaptic Hash Cache to throttle repetitive cross-modal empathy lookups
        self._resonance_cache: Dict[int, float] = {}

        # SYNAPTIC NEUROPLASTICITY BRIDGE BOOTSTRAP: Seed default profile states instantly if engram nodes exist
        if not self.style_path.exists() and self.engram_path.exists():
            try:
                with open(self.engram_path, "r", encoding="utf-8") as f:
                    engram_data = json.load(f)
                if isinstance(engram_data, dict) and "code_conventions" in engram_data:
                    self.style_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.style_path, "w", encoding="utf-8") as f:
                        json.dump(engram_data, f, indent=2)
            except Exception:
                pass

    def observe_and_record(
        self, agent_id: str, objective: str, successful_steps: List[str]
    ) -> None:
        """Captures a successful peer multi-agent interaction sequence to establish behavioral memory.

        Utilizes an out-of-place temporary file rewrite and atomic replacement to prevent log file corruption.
        """
        if not successful_steps:
            return

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_objective = objective.strip().lower().replace("\\", "/")
        sanitized_steps = [str(step).replace("\\", "/") for step in successful_steps]

        records: List[Dict[str, Any]] = []
        found_existing = False

        if self.log_path.exists():
            with BiologicalLock(str(self.log_path)):
                try:
                    with open(self.log_path, "r", encoding="utf-8") as f:
                        for line in f:
                            clean_line = line.strip()
                            if not clean_line:
                                continue
                            rec = json.loads(clean_line)
                            if rec.get("objective_slug") == normalized_objective:
                                rec["resonance_score"] = round(
                                    rec.get("resonance_score", 1.0) + 0.5, 2
                                )
                                rec["parameterized_chain"] = sanitized_steps
                                rec["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                                found_existing = True
                            records.append(rec)
                except Exception:
                    pass

        if not found_existing:
            observation_payload = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "observed_agent": str(agent_id),
                "objective_slug": normalized_objective,
                "parameterized_chain": sanitized_steps,
                "resonance_score": 1.0,
            }
            records.append(observation_payload)

        # ATOMIC REWRITE PROTOCOL: Stage updates via temporary buffer swaps to maintain zero-debt system states
        tmp_log_path = self.log_path.with_suffix(".tmp")
        with BiologicalLock(str(self.log_path)):
            try:
                with open(tmp_log_path, "w", encoding="utf-8") as f:
                    for r in records:
                        f.write(json.dumps(r) + "\n")
                os.replace(tmp_log_path, self.log_path)
            except Exception:
                if tmp_log_path.exists():
                    try:
                        os.remove(tmp_log_path)
                    except OSError:
                        pass
                raise

        console.print(
            f"[bold green]🧠 Mirror Neurons: Synaptic weight for '{normalized_objective}' potentiated cleanly and atomized.[/bold green]"
        )

    def synchronize_muscle_memory(self, prompt: str) -> Optional[List[str]]:
        """Scans recorded peer behaviors to derive an optimal local shell execution track shortcut."""
        if not self.log_path.exists():
            return None

        normalized_prompt = prompt.strip().lower().replace("\\", "/")
        result_chain: Optional[List[str]] = None

        with BiologicalLock(str(self.log_path)):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        clean_line = line.strip()
                        if not clean_line:
                            continue
                        record = json.loads(clean_line)
                        if record.get("objective_slug") == normalized_prompt:
                            result_chain = list(record["parameterized_chain"])
            except Exception:
                pass

        return result_chain

    # =====================================================================
    # STYLISTIC IMITATION LAYER (Resilient Token & Markdown AST Processing)
    # =====================================================================

    def _parse_metrics_isolated(
        self, sample_text: str, mode: str = "code"
    ) -> Dict[str, Any]:
        """Internal helper to isolate parsing analytics cleanly using standard lexers and markdown block tools."""
        metrics: Dict[str, Any] = {
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
        }

        MAX_SAMPLE_LINES = 2000
        raw_lines = sample_text.splitlines()
        if len(raw_lines) > MAX_SAMPLE_LINES:
            sample_text = "\n".join(raw_lines[:MAX_SAMPLE_LINES])

        if mode == "code":
            try:
                token_stream = list(
                    tokenize.generate_tokens(io.StringIO(sample_text).readline)
                )
                indent_tokens = [t for t in token_stream if t.type == tokenize.INDENT]
                if indent_tokens:
                    first_indent_str = indent_tokens[0].string
                    if "\t" in first_indent_str:
                        metrics["code_conventions"]["indentation"] = "tabs"
                    else:
                        metrics["code_conventions"]["indentation"] = (
                            f"{len(first_indent_str)}-spaces"
                        )

                for idx, tok in enumerate(token_stream):
                    if tok.type == tokenize.NAME and tok.string == "def":
                        if (
                            idx + 1 < len(token_stream)
                            and token_stream[idx + 1].type == tokenize.NAME
                        ):
                            func_name = token_stream[idx + 1].string

                            if re.search(r"[a-z]+[A-Z]", func_name):
                                metrics["code_conventions"]["naming"] = "camelCase"
                            elif "_" in func_name:
                                metrics["code_conventions"]["naming"] = "snake_case"

                            lookup_idx = idx + 2
                            while (
                                lookup_idx < len(token_stream)
                                and token_stream[lookup_idx].string != ":"
                            ):
                                lookup_idx += 1

                            if lookup_idx + 1 < len(token_stream):
                                check_idx = lookup_idx + 1
                                if token_stream[check_idx].type in (
                                    tokenize.NEWLINE,
                                    tokenize.NL,
                                ):
                                    check_idx += 1
                                if (
                                    check_idx < len(token_stream)
                                    and token_stream[check_idx].type == tokenize.INDENT
                                ):
                                    check_idx += 1
                                if (
                                    check_idx < len(token_stream)
                                    and token_stream[check_idx].type == tokenize.STRING
                                ):
                                    metrics["code_conventions"]["docstrings"] = True

            except (tokenize.TokenError, IndentationError):
                pass
            except Exception:
                pass

        elif mode == "prose":
            lines = sample_text.splitlines()
            bullet_counts: Dict[str, int] = {"-": 0, "*": 0, "+": 0, "ordered": 0}
            indent_counts = {"2-spaces": 0, "4-spaces": 0, "tabs": 0}
            bold_counts = {"asterisks": 0, "underscores": 0}
            italics_counts = {"asterisks": 0, "underscores": 0}
            has_callout = False
            has_expressive = False
            in_code_block = False

            for line in lines:
                stripped = line.strip()

                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue

                if in_code_block or not stripped:
                    continue

                if stripped.startswith(">"):
                    if "[!" in stripped:
                        has_callout = True
                    stripped = re.sub(r"^>\s*", "", stripped)
                    if not stripped:
                        continue

                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    if "\t" in line[:leading_spaces]:
                        indent_counts["tabs"] += 1
                    elif leading_spaces == 2:
                        indent_counts["2-spaces"] += 1
                    elif leading_spaces == 4:
                        indent_counts["4-spaces"] += 1

                if stripped.startswith("#"):
                    continue

                # RESOLUTION (Custom Checklist Theme Layouts): Parse checkboxes and multi-line ordered item intersections accurately
                if stripped.startswith("- ") or re.match(r"^-\s+\[[^\]]\]", stripped):
                    bullet_counts["-"] += 1
                elif stripped.startswith("* "):
                    bullet_counts["*"] += 1
                elif stripped.startswith("+ "):
                    bullet_counts["+"] += 1
                elif re.match(r"^\d+\.\s+", stripped):
                    bullet_counts["ordered"] += 1

                if "**" in stripped:
                    bold_counts["asterisks"] += 1
                if "__" in stripped:
                    bold_counts["underscores"] += 1

                if re.search(r"(?<!\*)\*(?!\*)[^\*]+(?<!\*)\*(?!\*)", stripped):
                    italics_counts["asterisks"] += 1
                if re.search(r"(?<!_)_(?!_)[^_]+(?<!_)_(?!_)", stripped):
                    italics_counts["underscores"] += 1

                if "!" in stripped:
                    has_expressive = True

            dominant_bullet = "-"
            max_bullet = 0
            for bullet, count in bullet_counts.items():
                if count > max_bullet:
                    max_bullet = count
                    dominant_bullet = bullet

            dominant_indent = "4-spaces"
            max_indent = 0
            for indent, count in indent_counts.items():
                if count > max_indent:
                    max_indent = count
                    dominant_indent = indent

            dominant_bold = "asterisks"
            if bold_counts["underscores"] > bold_counts["asterisks"]:
                dominant_bold = "underscores"

            dominant_italics = "asterisks"
            if italics_counts["underscores"] > italics_counts["asterisks"]:
                dominant_italics = "underscores"

            metrics["prose_cadence"]["bullet_style"] = dominant_bullet
            metrics["prose_cadence"]["nested_indentation"] = dominant_indent
            metrics["prose_cadence"]["bold_preference"] = dominant_bold
            metrics["prose_cadence"]["italics_preference"] = dominant_italics
            if has_callout or has_expressive:
                metrics["prose_cadence"]["tone"] = (
                    "expressive" if has_expressive else "architectural"
                )

        return metrics

    def analyze_and_mirror_style(self, sample_text: str, mode: str = "code") -> None:
        """Parses individual file text frames to update style card metrics with momentum boundaries."""
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

        with _STYLE_MUTEX:
            if self.style_path.exists():
                try:
                    with open(self.style_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, dict):
                            fingerprint = loaded
                except Exception:
                    pass

        if "allostatic_momentum" not in fingerprint or not isinstance(
            fingerprint["allostatic_momentum"], dict
        ):
            fingerprint["allostatic_momentum"] = {}

        new_metrics = self._parse_metrics_isolated(sample_text, mode)

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

        # ATOMIC FILE SWAP: Commit fingerprint payload safely
        tmp_style_path = self.style_path.with_suffix(".tmp")
        with _STYLE_MUTEX:
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
                    raise

    def consolidate_stylistic_baseline(self) -> None:
        """Crawls workspace core domains, samples files, and aggregates a plurality consensus to settle code/prose fingerprints."""
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
                            res = self._parse_metrics_isolated(content, mode="code")
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
                            res = self._parse_metrics_isolated(content, mode="prose")
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

        # ATOMIC FILE SWAP FOR CONSENSUS CONSOLIDATION
        tmp_style_path = self.style_path.with_suffix(".tmp")
        with _STYLE_MUTEX:
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
                    raise

        # THE SYNAPTIC NEUROPLASTICITY BRIDGE: Serialize consolidated rules to independent engrams
        long_term_payload: Dict[str, Any] = {
            "code_conventions": fingerprint.get("code_conventions", {}),
            "prose_cadence": fingerprint.get("prose_cadence", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.engram_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_engram_path = self.engram_path.with_suffix(".tmp")
        with _STYLE_MUTEX:
            with BiologicalLock(str(self.engram_path)):
                try:
                    with open(tmp_engram_path, "w", encoding="utf-8") as f:
                        json.dump(long_term_payload, f, indent=2)
                    os.replace(tmp_engram_path, self.engram_path)
                except Exception:
                    if tmp_engram_path.exists():
                        try:
                            os.remove(tmp_engram_path)
                        except OSError:
                            pass

        # ⚡ RESOLUTION (Synaptic Cache Eviction Flush): Clear caches upon structural updates
        self._resonance_cache.clear()

    def calculate_empathy_resonance(
        self, sample_text: str, mode: str = "code"
    ) -> float:
        """Computes a stylistic alignment score (0.0 to 0.5) against the active style fingerprint.

        SYNAPTIC CACHE EVICTION CEILING: Bounds in-memory maps to a maximum threshold, automatically purging the oldest
        500 entries via FIFO dict insertion indexes to protect systems from memory leaks.
        """
        text_hash = hash(sample_text)
        if text_hash in self._resonance_cache:
            return self._resonance_cache[text_hash]

        if not self.style_path.exists():
            return 0.0

        try:
            with open(self.style_path, "r", encoding="utf-8") as f:
                fp = json.load(f)
        except Exception:
            return 0.0

        # Dynamic Memory Shifting Eviction Boundary Pass
        if len(self._resonance_cache) >= 2000:
            for _ in range(500):
                if self._resonance_cache:
                    oldest_key = next(iter(self._resonance_cache))
                    self._resonance_cache.pop(oldest_key, None)

        observed = self._parse_metrics_isolated(sample_text, mode=mode)
        matches = 0
        total_keys = 0

        group = "code_conventions" if mode == "code" else "prose_cadence"
        if isinstance(fp, dict) and group in fp and group in observed:
            fp_group = fp[group]
            if isinstance(fp_group, dict):
                for k in observed[group]:
                    total_keys += 1
                    if fp_group.get(k) == observed[group][k]:
                        matches += 1

        if total_keys == 0:
            return 0.0

        score = round((matches / total_keys) * 0.5, 2)
        self._resonance_cache[text_hash] = score
        return score

    def inject_stylistic_prompt_context(
        self, domain_or_path: Optional[str] = None
    ) -> str:
        """Returns a string block describing your structural style to steer model outputs flawlessly."""
        base_fingerprint: Dict[str, Any] = {
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
        }

        if self.style_path.exists():
            try:
                with open(self.style_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        base_fingerprint = loaded
            except Exception:
                pass

        if domain_or_path:
            target_path = (
                Path(self.vault_path) / domain_or_path
                if not os.path.isabs(str(domain_or_path))
                else Path(str(domain_or_path))
            )
            sample_file: Optional[Path] = None

            if target_path.exists():
                if target_path.is_file() and target_path.suffix in (".py", ".md"):
                    sample_file = target_path
                elif target_path.is_dir():
                    valid_files = sorted(
                        [
                            p
                            for p in target_path.rglob("*")
                            if p.is_file() and p.suffix in (".py", ".md")
                        ],
                        key=lambda p: p.stat().st_mtime,
                        reverse=True,
                    )
                    if valid_files:
                        sample_file = valid_files[0]

            if sample_file:
                try:
                    content = sample_file.read_text(encoding="utf-8")
                    mode = "code" if sample_file.suffix == ".py" else "prose"
                    local_metrics = self._parse_metrics_isolated(content, mode=mode)

                    cc_target = base_fingerprint.get("code_conventions")
                    pc_target = base_fingerprint.get("prose_cadence")
                    if isinstance(cc_target, dict) and mode == "code":
                        cast(Dict[str, Any], cc_target).update(
                            local_metrics["code_conventions"]
                        )
                    if isinstance(pc_target, dict) and mode == "prose":
                        cast(Dict[str, Any], pc_target).update(
                            local_metrics["prose_cadence"]
                        )
                except Exception:
                    pass

        cc_final = base_fingerprint.get("code_conventions")
        pc_final = base_fingerprint.get("prose_cadence")

        cc = cast(
            Dict[str, Any],
            cc_final
            if isinstance(cc_final, dict)
            else base_fingerprint["code_conventions"],
        )
        pc = cast(
            Dict[str, Any],
            pc_final
            if isinstance(pc_final, dict)
            else base_fingerprint["prose_cadence"],
        )

        return (
            f"\n[STRICT MIRROR STYLE OVERRIDE]\n"
            f"- Code Indentation Layout: {cc.get('indentation')}\n"
            f"- Function Naming System: {cc.get('naming')}\n"
            f"- Mandatory Docstring Signatures: {cc.get('docstrings')}\n"
            f"- Text Formatting Preference: Bullet type '{pc.get('bullet_style')}' with a {pc.get('tone')} cadence.\n"
            f"- Nested Indentation Standard: {pc.get('nested_indentation')}\n"
            f"- Bold Formatting Syntactic Element: {pc.get('bold_preference')}\n"
            f"- Italics Formatting Syntactic Element: {pc.get('italics_preference')}\n"
        )
