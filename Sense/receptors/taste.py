import csv
import json
import zipfile
import sqlite3
import re
import struct
from pathlib import Path
from typing import Dict, Any
from System.ast_parser import extract_signatures


def sample_file(filepath: str) -> Dict[str, Any]:
    """
    The Gustatory Receptor (Taste) v4.
    Features: Poison Rejector, Gag Reflex, API Sommelier, Office Umami,
    Base64 Gag Reflex, Bitter Receptors, Archive Tasting, Schema Tasting,
    AST Code Skeletons, Media Metadata Tasting, and Semantic Markdown Tables.
    """
    target = Path(filepath).resolve()

    if not target.exists() or not target.is_file():
        return {"error": f"File not found or is a directory: {filepath}"}

    size_mb = target.stat().st_size / (1024 * 1024)
    extension = target.suffix.lower()
    file_name_lower = target.name.lower()

    profile: Dict[str, Any] = {
        "file_name": target.name,
        "extension": extension,
        "size_mb": round(size_mb, 2),
        "format_type": "unknown",
        "content_sample": "",
    }

    # 1. POISON REJECTOR (Hardcoded Secret Protection)
    POISON_NAMES = {".env", ".pem", "id_rsa"}
    if (
        file_name_lower in POISON_NAMES
        or "secret" in file_name_lower
        or "credential" in file_name_lower
    ):
        profile["format_type"] = "indigestible"
        profile["content_sample"] = (
            f"[POISON DETECTED]: Refusing to ingest security credentials ({target.name}) into LLM memory."
        )
        return profile

    # 2. THE GAG REFLEX (Protect RAM and Context Window)
    if size_mb > 50.0:
        profile["format_type"] = "indigestible"
        profile["content_sample"] = (
            f"[GAG REFLEX]: File is {round(size_mb, 2)}MB. Too large to safely ingest into memory."
        )
        return profile

    # 3. MEDIA METADATA TASTING (Extract stats without reading binary payload)
    MEDIA_BINARIES = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".mp3",
        ".mp4",
        ".wav",
        ".avi",
        ".mov",
        ".mkv",
    }
    if extension in MEDIA_BINARIES:
        profile["format_type"] = "media_metadata"
        meta = [
            f"File: {target.name}",
            f"Size: {round(size_mb, 2)} MB",
            f"Type: Binary Media ({extension})",
        ]
        try:
            with open(target, "rb") as f:
                head = f.read(24)
                if extension == ".png" and head.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
                    check = f.read(8)
                    if len(check) == 8:
                        w, h = struct.unpack(">II", check)
                        meta.append(f"Dimensions: {w}x{h} pixels")
                elif extension == ".gif" and head.startswith(b"GIF8"):
                    w, h = struct.unpack("<HH", head[6:10])
                    meta.append(f"Dimensions: {w}x{h} pixels")
                elif extension == ".wav" and head.startswith(b"RIFF"):
                    meta.append("Format: RIFF/WAV Audio")
        except Exception:
            pass
        profile["content_sample"] = "[MEDIA METADATA TASTED]\\n" + "\\n".join(meta)
        return profile

    INDIGESTIBLE_BINARIES = {".exe", ".dll", ".so", ".dylib", ".bin", ".iso", ".dmg"}
    if extension in INDIGESTIBLE_BINARIES:
        profile["format_type"] = "indigestible"
        profile["content_sample"] = (
            f"[GAG REFLEX]: {extension} is a compiled binary. Indigestible."
        )
        return profile

    try:
        # 4. AST CODE SKELETONS
        if extension in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            profile["format_type"] = "code_skeleton"
            signatures = extract_signatures(str(target))
            if signatures:
                profile["content_sample"] = f"[AST SKELETON EXTRACTED]\\n{signatures}"
            else:
                with open(target, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                profile["content_sample"] = content[:4000] + (
                    "\\n... [TRUNCATED]" if len(content) > 4000 else ""
                )

        # 5. API SOMMELIER (Swagger / OpenAPI Distillation)
        elif file_name_lower in {"swagger.json", "openapi.json", "openapi.yaml"}:
            profile["format_type"] = "api_spec"
            with open(target, "r", encoding="utf-8") as f:
                spec = json.load(f)
                endpoints = []
                for path, methods in spec.get("paths", {}).items():
                    for method, details in methods.items():
                        summary = details.get("summary", "No summary")
                        endpoints.append(f"{method.upper()} {path} - {summary}")
            profile["content_sample"] = (
                "[API SOMMELIER: Extracted Endpoints]\\n" + "\\n".join(endpoints)
            )

        # 6. OFFICE UMAMI (docx & xlsx without dependencies!)
        elif extension in {".docx", ".xlsx"}:
            profile["format_type"] = "office_document"
            with zipfile.ZipFile(target, "r") as z:
                if extension == ".docx":
                    xml_content = z.read("word/document.xml").decode("utf-8")
                else:  # .xlsx
                    xml_content = z.read("xl/sharedStrings.xml").decode("utf-8")
                clean_text = re.sub(r"<[^>]+>", " ", xml_content)
                clean_text = re.sub(r"\\s+", " ", clean_text).strip()
                profile["content_sample"] = clean_text[:4000] + (
                    "\\n... [TRUNCATED]" if len(clean_text) > 4000 else ""
                )

        # 7. BASE64 GAG REFLEX (.ipynb & .svg)
        elif extension == ".ipynb":
            profile["format_type"] = "jupyter_notebook"
            with open(target, "r", encoding="utf-8") as f:
                nb = json.load(f)
                extracted = []
                for cell in nb.get("cells", []):
                    if cell.get("cell_type") == "markdown":
                        extracted.append("".join(cell.get("source", [])))
                    elif cell.get("cell_type") == "code":
                        extracted.append(
                            "```python\\n" + "".join(cell.get("source", [])) + "\\n```"
                        )
                        for out in cell.get("outputs", []):
                            if "data" in out and "image/png" in out["data"]:
                                extracted.append("[OUTPUT: BASE64 IMAGE OMITTED]")
                            elif "text" in out:
                                extracted.append("".join(out.get("text", [])))
            full_text = "\\n\\n".join(extracted)
            profile["content_sample"] = full_text[:4000] + (
                "\\n... [TRUNCATED]" if len(full_text) > 4000 else ""
            )

        elif extension == ".svg":
            profile["format_type"] = "vector_graphic"
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                svg = f.read()
                svg = re.sub(r'd="[^"]{50,}"', 'd="[BASE64 PATH OMITTED]"', svg)
                profile["content_sample"] = svg[:4000] + (
                    "\\n... [TRUNCATED]" if len(svg) > 4000 else ""
                )

        # 8. CRUNCHY (Archive Tasting)
        elif extension == ".zip":
            profile["format_type"] = "archive_manifest"
            with zipfile.ZipFile(target, "r") as z:
                files = z.namelist()
                sample = "\\n".join(files[:50])
                if len(files) > 50:
                    sample += (
                        f"\\n\\n... [TRUNCATED: {len(files) - 50} more files inside]"
                    )
            profile["content_sample"] = sample

        # 9. MEMORY TASTING (SQLite Schema)
        elif extension in {".sqlite", ".db", ".sqlite3"}:
            profile["format_type"] = "database_schema"
            conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL;"
            )
            schemas = [
                f"--- {row[0].upper()}: {row[1]} ---\\n{row[2]}"
                for row in cursor.fetchall()
            ]
            conn.close()
            profile["content_sample"] = (
                "\\n\\n".join(schemas) if schemas else "Empty database."
            )

        # 10. UMAMI (Documents)
        elif extension == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(target))
            pdf_text = [
                f"--- Page {i + 1} ---\\n{page.extract_text()}"
                for i, page in enumerate(reader.pages[:10])
            ]
            profile["format_type"] = "document"
            profile["content_sample"] = "\\n".join(pdf_text) + (
                "\\n\\n... [TRUNCATED]" if len(reader.pages) > 10 else ""
            )

        # 11. SWEET (Semantic Markdown Tables for CSVs)
        elif extension == ".csv":
            profile["format_type"] = "structured_data"
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                profile["content_sample"] = "Empty CSV."
            else:
                headers = rows[0]
                md_table = [
                    "| " + " | ".join(headers) + " |",
                    "|" + "|".join(["---"] * len(headers)) + "|",
                ]
                for row in rows[1:11]:
                    # Pad the row if it's missing columns to maintain Markdown compliance
                    row += [""] * (len(headers) - len(row))
                    md_table.append("| " + " | ".join(row[: len(headers)]) + " |")

                profile["content_sample"] = "\\n".join(md_table)
                if len(rows) > 11:
                    profile["content_sample"] += (
                        f"\\n... [TRUNCATED: {len(rows) - 11} remaining rows skipped]"
                    )

        elif extension == ".json":
            if size_mb > 5.0:
                profile["format_type"] = "raw_text"
                with open(target, "r", encoding="utf-8", errors="ignore") as f:
                    profile["content_sample"] = (
                        f.read(4000) + "\\n... [TRUNCATED: JSON too large]"
                    )
            else:
                with open(target, "r", encoding="utf-8") as f:
                    dump = json.dumps(json.load(f), indent=2)
                profile["format_type"] = "structured_data"
                profile["content_sample"] = dump[:2000] + (
                    "\\n... [TRUNCATED]" if len(dump) > 2000 else ""
                )

        # 12. BITTER (Log Distillation & Raw Text)
        else:
            profile["format_type"] = "raw_text"
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if extension == ".log":
                lines = content.split("\\n")
                errors = [
                    line
                    for line in lines
                    if re.search(r"(?i)(error|exception|fatal|fail|traceback)", line)
                ]
                if errors:
                    err_sample = "\\n".join(errors[:50])
                    profile["content_sample"] = (
                        f"[LOG DISTILLATION: Extracted Errors]\\n{err_sample}\\n\\n... [FIBER REMOVED]"
                    )
                    return profile

            if len(content) > 10000:
                profile["content_sample"] = (
                    f"{content[:4000]}\\n\\n... [OMITTED: {len(content) - 8000} bytes] ...\\n\\n{content[-4000:]}"
                )
            else:
                profile["content_sample"] = content

    except Exception as e:
        profile["error"] = f"Extraction failed: {str(e)}"

    return profile
