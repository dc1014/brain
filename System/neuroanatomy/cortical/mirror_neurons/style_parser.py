import io
import re
import tokenize
from typing import Dict, Any


class CorticalStyleParser:
    """Isolates low-level lexical token extraction and micro-AST markdown block profiling operations."""

    @staticmethod
    def parse_metrics_isolated(sample_text: str, mode: str = "code") -> Dict[str, Any]:
        """Profiles layout typography rules across code arrays or structured prose files flawlessly."""
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
