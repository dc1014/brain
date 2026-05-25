from System.core.paths import ROOT_DIR
from Sense.receptors.smell import smell_environment


def process_scent_profile(target_dir: str = ".") -> str:
    target_path = ROOT_DIR / target_dir
    raw_data = smell_environment(str(target_path))

    if "error" in raw_data:
        return (
            f"<olfactory_report status='error'>{raw_data['error']}</olfactory_report>"
        )

    anomalies = []

    if raw_data.get("toxic_rot"):
        toxic_str = "\n".join(raw_data["toxic_rot"])
        anomalies.append(
            f"<toxic_rot instructions='URGENT: ALERT USER. REMOVE SECRET FROM FILE.'>\n{toxic_str}\n</toxic_rot>"
        )

    if raw_data.get("git_conflict_rot"):
        conflict_str = "\n".join(raw_data["git_conflict_rot"])
        anomalies.append(
            f"<git_conflict_rot instructions='URGENT: Use read_safe_file and write_safe_file to resolve the git merge conflict markers.'>\n{conflict_str}\n</git_conflict_rot>"
        )

    if raw_data.get("structural_rot"):
        struct_str = "\n".join(raw_data["structural_rot"])
        anomalies.append(
            f"<structural_rot instructions='Use write_safe_file to add the missing closing `---` to the YAML frontmatter.'>\n{struct_str}\n</structural_rot>"
        )

    if raw_data.get("code_rot"):
        rot_str = "\n".join(raw_data["code_rot"])
        anomalies.append(
            f"<code_rot instructions='REVIEW_AND_REFACTOR'>\n{rot_str}\n</code_rot>"
        )

    if raw_data.get("cognitive_rot"):
        cog_str = "\n".join(raw_data["cognitive_rot"])
        anomalies.append(
            f"<cognitive_rot instructions='REVIEW_RECOMMENDED. Use write_safe_file to clean up stale TODOs.'>\n{cog_str}\n</cognitive_rot>"
        )

    if raw_data.get("empty_files"):
        files_str = "\n".join(raw_data["empty_files"])
        anomalies.append(
            f"<semantic_rot type='empty_files' instructions='DELETE_RECOMMENDED'>\n{files_str}\n</semantic_rot>"
        )

    if raw_data.get("broken_links"):
        links_str = "\n".join(raw_data["broken_links"])
        anomalies.append(
            f"<semantic_rot type='broken_links' instructions='DO NOT DELETE FILE. Use read_safe_file and write_safe_file to fix the text.'>\n{links_str}\n</semantic_rot>"
        )

    if raw_data.get("dead_media"):
        media_str = "\n".join(raw_data["dead_media"])
        anomalies.append(
            f"<media_rot type='zero_byte' instructions='DELETE_RECOMMENDED'>\n{media_str}\n</media_rot>"
        )

    if raw_data.get("orphaned_media"):
        orphan_str = "\n".join(raw_data["orphaned_media"])
        anomalies.append(
            f"<media_rot type='orphaned' instructions='DELETE_RECOMMENDED'>\n{orphan_str}\n</media_rot>"
        )

    if raw_data.get("duplicate_files"):
        dup_str = "\n".join(raw_data["duplicate_files"])
        anomalies.append(
            f"<duplicate_rot instructions='DELETE_RECOMMENDED_FOR_ALL_BUT_ONE'>\n{dup_str}\n</duplicate_rot>"
        )

    if raw_data.get("digital_dust"):
        dust_str = "\n".join(raw_data["digital_dust"])
        anomalies.append(
            f"<digital_dust instructions='DELETE_RECOMMENDED. These are temporary or system junk files.'>\n{dust_str}\n</digital_dust>"
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
