from System.tools import ROOT_DIR
from Sense.receptors.smell import smell_environment


def process_scent_profile(target_dir: str = ".") -> str:  # <--- Changed default to "."
    """
    The Olfactory Bulb.
    Receives raw chemical data from the Nose, transduces it into memory,
    and writes it directly to the Meta directory for the Swarm to triage during sleep.
    """
    target_path = ROOT_DIR / target_dir
    raw_data = smell_environment(str(target_path))

    if "error" in raw_data:
        return (
            f"<olfactory_report status='error'>{raw_data['error']}</olfactory_report>"
        )

    anomalies = []

    if raw_data.get("code_rot"):
        rot_str = "\n".join(raw_data["code_rot"])
        anomalies.append(f"<code_rot>\n{rot_str}\n</code_rot>")
    if raw_data.get("empty_files"):
        files_str = "\n".join(raw_data["empty_files"])
        anomalies.append(
            f"<semantic_rot type='empty_files' instructions='DELETE_RECOMMENDED'>\n{files_str}\n</semantic_rot>"
        )
    if raw_data.get("broken_links"):
        links_str = "\n".join(raw_data["broken_links"])
        # SHIFT-LEFT: Explicitly tell the LLM not to delete files just because they have a bad link!
        anomalies.append(
            f"<semantic_rot type='broken_links' instructions='DO NOT DELETE FILE. Use read_safe_file and write_safe_file to fix the text.'>\n{links_str}\n</semantic_rot>"
        )
    if raw_data.get("dead_media"):
        media_str = "\n".join(raw_data["dead_media"])
        anomalies.append(
            f"<media_rot type='zero_byte' instructions='DELETE_RECOMMENDED'>\n{media_str}\n</media_rot>"
        )

    if not anomalies:
        report = "<olfactory_report status='clean'>No detectable rot or anomalies.</olfactory_report>"
    else:
        report = (
            "<olfactory_report status='anomalies_detected'>\n"
            + "\n".join(anomalies)
            + "\n</olfactory_report>"
        )

    meta_dir = ROOT_DIR / "Meta"
    meta_dir.mkdir(exist_ok=True)
    report_file = meta_dir / "Olfactory_Anomalies.md"

    report_file.write_text(
        f"# Olfactory Scent Report\n*Autonomously generated static analysis. Swarm agents should follow the XML instructions to resolve rot.*\n\n```xml\n{report}\n```\n",
        encoding="utf-8",
    )

    return report
