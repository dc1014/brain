import csv
import json
import zipfile
import sqlite3
import re
import struct
from pathlib import Path
from typing import Dict, Any, Union
from System.ast_parser import extract_signatures


def sample_file(filepath: Union[str, Path]) -> Dict[str, Any]:
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
        or extension == ".key"
        or "secret" in file_name_lower
    ):
        profile["format_type"] = "indigestible"
        profile["content_sample"] = (
            "[GAG REFLEX] POISON DETECTED: Private credentials, environment keys, or authentication tokens cannot be exposed to active context layers."
        )
        return profile

    # 2. GAG REFLEX (Massive Binary File Protection)
    if size_mb > 15.0 and extension not in {".db", ".sqlite", ".csv"}:
        profile["format_type"] = "indigestible"
        profile["content_sample"] = (
            f"[GAG REFLEX] File size ({profile['size_mb']} MB) exceeds safe context window limits for raw ingestion."
        )
        return profile

    try:
        # 3. API SOMMELIER (OpenAPI Spec Ingestion)
        if file_name_lower in {"openapi.json", "swagger.json"} or (
            extension == ".json" and "openapi" in file_name_lower
        ):
            # Clamped strictly with encoding declaration to withstand the Windows Trap
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                profile["format_type"] = "api_spec"
                routes_summary = []
                paths = data.get("paths", {})
                for path, methods in paths.items():
                    for method, info in methods.items():
                        summary = info.get("summary", info.get("description", ""))
                        routes_summary.append(f"{method.upper()} {path} - {summary}")
                profile["content_sample"] = "\n".join(routes_summary[:100])
                return profile

        # 4. PDF (Office Umami)
        elif extension == ".pdf":
            try:
                from PyPDF2 import PdfReader

                reader = PdfReader(target)
                pages = reader.pages
                text = "".join([page.extract_text() or "" for page in pages])
                profile["format_type"] = "office_document"
                profile["content_sample"] = text[:2000] + (
                    "\n... [TRUNCATED]" if len(text) > 2000 else ""
                )
            except ImportError:
                profile["content_sample"] = "[PDF PARSING REQUIRES PyPDF2]"
            except Exception as e:
                profile["content_sample"] = f"[PDF PARSING FAILED: {str(e)}]"

        # 5. OFFICE UMAMI (Docx / XLSX parsing)
        elif extension == ".docx":
            with zipfile.ZipFile(target) as z:
                doc_xml = z.read("word/document.xml").decode("utf-8")
                text_runs = re.findall(r"<w:t.*?>(.*?)</w:t>", doc_xml)
                clean_text = " ".join(text_runs)
                profile["format_type"] = "office_document"
                profile["content_sample"] = clean_text[:2000]

        # 6. BASE64 GAG REFLEX (Jupyter Notebook Image Stripping)
        elif extension == ".ipynb":
            with open(target, "r", encoding="utf-8") as f:
                nb = json.load(f)
            profile["format_type"] = "notebook"
            clean_cells = []
            for cell in nb.get("cells", []):
                if cell.get("cell_type") == "code":
                    source = "".join(cell.get("source", []))
                    clean_cells.append(source)
                    for output in cell.get("outputs", []):
                        if "data" in output and "image/png" in output["data"]:
                            clean_cells.append("[OUTPUT: BASE64 IMAGE OMITTED]")
                else:
                    source = "".join(cell.get("source", []))
                    clean_cells.append(source)
            profile["content_sample"] = "\n\n".join(clean_cells)[:4000]

        # 7. ARCHIVE TASTING (ZIP Inspection)
        elif extension == ".zip":
            with zipfile.ZipFile(target) as z:
                namelist = z.namelist()
                profile["format_type"] = "archive"
                profile["content_sample"] = (
                    f"[ARCHIVE MANIFEST]\nTotal Files: {len(namelist)}\n"
                    + "\n".join(namelist[:50])
                )

        # 8. SCHEMA TASTING (SQLite Databases)
        elif extension in {".db", ".sqlite", ".sqlite3"}:
            conn = sqlite3.connect(target)
            cursor = conn.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            profile["format_type"] = "database_schema"
            schema_dump = []
            for table_name, sql in tables:
                schema_dump.append(f"Table: {table_name}\nSchema: {sql}")
            profile["content_sample"] = "\n\n".join(schema_dump)[:4000]

        # 9. AST CODE SKELETONS (Python Code Structuring)
        elif extension == ".py":
            with open(target, "r", encoding="utf-8") as f:
                code_content = f.read()
            profile["format_type"] = "code_skeleton"
            profile["content_sample"] = extract_signatures(code_content)

        # 10. MEDIA METADATA TASTING (PNG/JPG Header Parsing)
        elif extension == ".png":
            with open(target, "rb") as f:
                header = f.read(24)
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                width, height = struct.unpack(">II", header[16:24])
                profile["format_type"] = "media_metadata"
                profile["content_sample"] = (
                    f"[MEDIA METADATA TASTED]\nFile: {target.name}\nSize: {profile['size_mb']} MB\nType: Binary Media (.png)\nDimensions: {width}x{height} pixels"
                )
            else:
                profile["format_type"] = "media_metadata"
                profile["content_sample"] = (
                    f"Binary file metadata: {target.name} ({profile['size_mb']} MB)"
                )

        # 11. SEMANTIC MARKDOWN TABLES (CSV Formatter)
        elif extension == ".csv":
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                reader_csv = csv.reader(f)
                rows = list(reader_csv)
            profile["format_type"] = "structured_data"
            if rows:
                headers = rows[0]
                markdown_table = [
                    "| " + " | ".join(headers) + " |",
                    "| " + " | ".join(["---"] * len(headers)) + " |",
                ]
                for row in rows[1:15]:
                    markdown_table.append("| " + " | ".join(row) + " |")
                profile["content_sample"] = "\n".join(markdown_table)
            else:
                profile["content_sample"] = "[EMPTY CSV DATA]"

        # 12. BITTER (Log Distillation & Raw Text)
        else:
            profile["format_type"] = "raw_text"
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if extension == ".log":
                lines = content.split("\n")
                errors = [
                    line
                    for line in lines
                    if re.search(r"(?i)(error|exception|fatal|fail|traceback)", line)
                ]
                if errors:
                    err_sample = "\n".join(errors[:50])
                    profile["content_sample"] = (
                        f"[LOG DISTILLATION: Extracted Errors]\n{err_sample}\n\n... [FIBER REMOVED]"
                    )
                    return profile

            if len(content) > 10000:
                profile["content_sample"] = (
                    f"{content[:4000]}\n\n... [OMITTED: {len(content) - 8000} bytes] ...\n\n{content[-4000:]}"
                )
            else:
                profile["content_sample"] = content

        return profile

    except Exception as e:
        profile["content_sample"] = (
            f"[SENSORY PROCESSING ERROR: catastrophic failure during structural file breakdown - {str(e)}]"
        )
        return profile
