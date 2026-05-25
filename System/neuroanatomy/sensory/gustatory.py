from Sense.receptors.taste import sample_file
from System.core.paths import ROOT_DIR


def process_taste_profile(filepath: str) -> str:
    """
    The Gustatory Bulb.
    Translates raw file extractions into an LLM-digestible XML snippet.
    """
    target_path = ROOT_DIR / filepath
    raw_data = sample_file(str(target_path))

    if "error" in raw_data:
        return f"<taste_profile status='error'>{raw_data['error']}</taste_profile>"

    file_name = raw_data.get("file_name", "unknown")
    format_type = raw_data.get("format_type", "unknown")
    size_mb = raw_data.get("size_mb", 0)
    content_sample = raw_data.get("content_sample", "")

    xml = f"""<taste_profile file="{file_name}" format="{format_type}" size_mb="{size_mb}">
<content_sample>
{content_sample}
</content_sample>
</taste_profile>"""

    return xml.strip()
