from System.core.paths import ROOT_DIR
import re
import time
import subprocess
from datetime import datetime


LOG_DIR = ROOT_DIR / "logs"


def check_and_run_sleep():
    """Circadian Rhythm: Runs at 2 AM. Checks backups to ensure it only runs once per day."""
    now = datetime.now()
    if now.hour < 2:
        return  # Too early in the day

    today_str = now.strftime("%Y-%m-%d")
    backup_dir = LOG_DIR / "backups"

    # If today's backup exists, we already slept.
    if backup_dir.exists() and list(backup_dir.glob(f"*_{today_str}.md")):
        return

    print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 🌙 Triggering Sleep Cycle...")
    subprocess.run(["uv", "run", "python", "System/cli.py", "sleep"])


def check_and_run_daydream():
    """Default Mode Network: Triggers if idle for 4 hours."""
    hippocampus = LOG_DIR / "agent_interactions.jsonl"
    daydreams = ROOT_DIR / "Personal" / "Scratchpad" / "Daydreams.md"

    now = time.time()
    if not hippocampus.exists():
        return

    last_interaction = hippocampus.stat().st_mtime
    idle_time = now - last_interaction

    if idle_time > (4 * 3600):  # 4 hours
        last_daydream = daydreams.stat().st_mtime if daydreams.exists() else 0

        # Ensure we haven't already daydreamed during this idle period
        if last_daydream < last_interaction:
            print(
                f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ☁️ Activating Default Mode Network..."
            )
            subprocess.run(
                ["uv", "run", "python", "System/cli.py", "daydream", "--domain", "META"]
            )

            # Touch the file to update its modified time, preventing infinite loops
            if daydreams.exists():
                daydreams.touch()


def check_and_run_forage():
    """Foraging Drive: Triggers every 12 hours."""
    briefing = ROOT_DIR / "Personal" / "Morning_Briefing.md"
    now = time.time()

    last_forage = briefing.stat().st_mtime if briefing.exists() else 0

    if (now - last_forage) > (12 * 3600):  # 12 hours
        print(
            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🌿 Triggering Subconscious Foraging..."
        )
        # You can hardcode a specific competitor URL or news site here
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "System/cli.py",
                "forage",
                "https://news.ycombinator.com",
                "--domain",
                "PERSONAL",
            ]
        )

        if briefing.exists():
            briefing.touch()


def run_pacemaker():
    print("🫀 Autonomic Nervous System Online. Listening for biological triggers...")
    while True:
        try:
            check_and_run_sleep()
            check_and_run_daydream()
            check_and_run_forage()
        except Exception as e:
            print(f"⚠️ Autonomic nervous system misfire: {e}")

        # Sleep for 5 minutes before checking the file system again
        time.sleep(300)


def consolidate_historical_facts(
    file_content: str, current_date: str, fact_type: str, new_value: str
) -> str:
    """Downtime cycle utility: Automatically limits active assertions by applying valid_until ranges.

    Args:
        file_content: Raw text content from the target node file.
        current_date: Chronological validation marker (e.g., '2026-05-19').
        fact_type: Attribute variable classification key.
        new_value: Numeric or narrative metric to attach.
    """
    pattern = rf'(<fact\s+type="{fact_type}"\s+value="[^"]+"\s+date="([^"]+)"(?![^>]*valid_until)[^>]*>)'

    # Locate fact metrics currently missing clear termination bounds
    matches = re.findall(pattern, file_content)
    updated_content = file_content

    for full_tag, start_date in matches:
        if start_date != current_date:
            # Swap out un-terminated boundaries for a cleanly limited definition matrix
            bounded_tag = full_tag.replace("/>", f' valid_until="{current_date}" />')
            updated_content = updated_content.replace(full_tag, bounded_tag)

    # Append the new fact record cleanly onto the base document landscape
    new_tag = f'\n<fact type="{fact_type}" value="{new_value}" date="{current_date}" />'
    return updated_content + new_tag


if __name__ == "__main__":
    run_pacemaker()
