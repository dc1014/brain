import json
import os
import re
import typer
import shutil
import subprocess
import yaml  # type: ignore
import sys
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from litellm import completion  # type: ignore

# --- SHIFT-LEFT: CROSS-PLATFORM ENCODING FIX ---
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore


from System.llm import LOG_FILE, log_interaction
from System.runtime import analyze_task, execute_pipeline

ROOT_DIR = Path(__file__).parent.parent

app = typer.Typer(help="Brain OS: The Multi-Agent Life Operating System")
console = Console()

CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        AGENT_CONFIG = yaml.safe_load(f)
except Exception as e:
    console.print(f"[bold red]Fatal Error loading agents.yaml:[/bold red] {e}")
    exit(1)


@app.command()
def task(
    description: str = typer.Argument(..., help="The task you want the AI to perform."),
    obsidian: bool = typer.Option(
        False,
        "--obsidian",
        help="Route task to the Pending Queue instead of terminal execution.",
    ),
    urgent: bool = typer.Option(
        False,
        "--urgent",
        help="Release Cortisol: Bypass safety gates and burn emergency tokens.",
    ),
    explore: bool = typer.Option(
        False,
        "--explore",
        help="Release Dopamine: Increase creativity and neural temperature.",
    ),
) -> None:
    from System.organs.endocrine import release_cortisol, release_dopamine

    if urgent is True:
        release_cortisol()
    if explore is True:
        release_dopamine()

    console.print(
        f"\n[bold green]🚀 Initializing Life OS task:[/bold green] '{description}'\n"
    )

    with console.status(
        # ... the rest of the function remains exactly the same ...
        "[bold yellow]🛡️ Dispatcher is analyzing the task...[/bold yellow]",
        spinner="dots",
    ):
        is_valid, reason, route_type, domain, dispatch_usage = analyze_task(description)

    if not is_valid:
        console.print(
            Panel(f"[bold red]Task Rejected:[/bold red] {reason}", border_style="red")
        )
        log_interaction(
            "Dispatcher (Bouncer)",
            AGENT_CONFIG["models"]["gpt_mini"],
            "Dispatcher Logic",
            description,
            f"REJECTED: {reason}",
            dispatch_usage,
            "REJECTED",
            "NONE",
        )
        return

    console.print(
        f"[dim]✅ Pre-Flight Passed. Assigned Route: [bold]{route_type}[/bold] | Domain Context: [bold cyan]{domain}[/bold cyan][/dim]"
    )

    # --- THE HANDOFF PROTOCOL (OBSIDIAN UI) ---
    if obsidian:
        pending_file = Path(__file__).parent.parent / "System" / "Pending_Actions.md"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        ticket = (
            f"\n### ⏳ Pending Task: {route_type}\n"
            f"**Logged:** {timestamp} | **Domain:** `{domain}`\n"
            f"**Prompt:** {description}\n"
            f"- [ ] **Status:** PENDING EXECUTION\n"
            f"---\n"
        )

        # Append mode ('a') stacks the tasks safely
        with open(pending_file, "a", encoding="utf-8") as f:
            f.write(ticket)

        console.print(
            "[bold green]✅ Task safely queued in System/Pending_Actions.md[/bold green]"
        )
        return  # Exit safely before executing!

    # --- STANDARD TERMINAL EXECUTION ---
    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    agents_to_run = [step["agent"] for step in pipeline]

    console.print("\n[bold yellow]⚠️  PIPELINE AUTHORIZATION[/bold yellow]")
    console.print(
        f"This task requires the [bold]{route_type}[/bold] route, which will wake up:"
    )
    console.print(f"[bold cyan]{' -> '.join(agents_to_run)}[/bold cyan]")

    try:
        auth = (
            input("\nAuthorize AI execution and token spend? [y/N]: ").strip().lower()
        )
    except (EOFError, KeyboardInterrupt):
        auth = "n"

    if auth not in ["y", "yes"]:
        console.print(
            "\n[bold red]🛑 Task Aborted: User declined pipeline execution.[/bold red]\n"
        )
        return

    execute_pipeline(description, route_type, domain)


@app.command()
def execute_pending() -> None:
    """Reads the Pending_Actions.md queue, executes all tasks sequentially, and clears the file."""
    # Tell downstream modules we are in a pre-approved headless UI state
    os.environ["BRAIN_OS_HEADLESS"] = "1"

    pending_file = Path(__file__).parent.parent / "System" / "Pending_Actions.md"
    # ... the rest of the function remains identical

    if not pending_file.exists() or pending_file.stat().st_size == 0:
        console.print("[yellow]No pending tasks found in queue.[/yellow]")
        return

    content = pending_file.read_text(encoding="utf-8")

    # Extract all the queued descriptions using Regex
    tasks_to_run = re.findall(r"\*\*Prompt:\*\* (.*)", content)

    if not tasks_to_run:
        console.print("[red]Could not parse any valid tasks from the file.[/red]")
        return

    console.print(
        f"[bold green]🚀 Found {len(tasks_to_run)} pending tasks. Executing sequence...[/bold green]"
    )

    for idx, task_desc in enumerate(tasks_to_run, 1):
        console.print(
            f"\n[bold blue]--- Executing Task {idx}/{len(tasks_to_run)} ---[/bold blue]"
        )

        # Re-analyze to ensure context is perfectly fresh before execution
        is_valid, reason, route_type, domain, _ = analyze_task(task_desc)
        if is_valid:
            execute_pipeline(task_desc, route_type, domain)
        else:
            console.print(
                f"[bold red]Task failed pre-flight validation:[/bold red] {reason}"
            )

    # THE WIPE: Overwrite the file with 'w' to reset it back to a clean state
    pending_file.write_text(
        "# ⚠️ Pending Execution Queue\n\n*Queue is currently empty.*\n", encoding="utf-8"
    )
    console.print(
        "\n[bold green]✅ Queue executed and cleared successfully![/bold green]"
    )


@app.command()
def forage(
    url: str = typer.Argument(..., help="The URL to forage for signals."),
    domain: str = typer.Option(
        "META", "--domain", "-d", help="The domain context to store the intel."
    ),
) -> None:
    """Biological Foraging: Gathers external signals and appends to the Morning Briefing."""
    console.print(
        f"\n[bold magenta]🌿 Initiating Subconscious Foraging for {domain}...[/bold magenta]"
    )
    os.environ["BRAIN_OS_HEADLESS"] = "1"

    prompt = f"Please forage this URL for high-signal intelligence: {url}"
    execute_pipeline(prompt, "SUBCONSCIOUS_FORAGE", domain.upper())


@app.command()
def daydream(
    domain: str = typer.Option(
        "META", "--domain", "-d", help="The domain to daydream about."
    ),
    code: bool = typer.Option(
        False,
        "--code",
        "-c",
        help="Enter REM Sleep: Allow Forge to autonomously write software prototypes.",
    ),
    project: str = typer.Option(
        "forge",
        "--project",
        "-p",
        help="The Studio project to dream in (required if --code is used).",
    ),
) -> None:
    """Default Mode Network: Synthesizes thoughts, or safely prototypes software via REM Paralysis."""
    from System.organs.pineal import is_host_asleep
    from System.organs.dmn import enforce_rem_paralysis

    # 1. Pineal Gland Check (Optional safeguard, mostly for autonomous pacemakers, but good to log)
    if not is_host_asleep(idle_hours_threshold=0.1):  # Just a check for demo purposes
        console.print(
            "[dim]Note: Host is active, but forcing Daydream state anyway.[/dim]"
        )

    if not code:
        # --- THOUGHT DREAMING (Passive, Safe) ---
        console.print(
            f"\n[bold magenta]☁️ Activating Default Mode Network ({domain}). Synthesizing thoughts...[/bold magenta]"
        )
        os.environ["BRAIN_OS_HEADLESS"] = "1"
        prompt = "Review our recent experiments and active memory. Synthesize a new strategic hypothesis and save it to the Daydreams file."
        execute_pipeline(prompt, "SUBCONSCIOUS_DAYDREAM", domain.upper())

    else:
        # --- REM SLEEP (Active Software Prototyping) ---
        console.print(
            "\n[bold magenta]💤 Entering REM Sleep. Forge is initiating autonomous software prototyping...[/bold magenta]"
        )

        # 1. Enforce REM Paralysis (Git Sandbox)
        branch = enforce_rem_paralysis(project)
        if not branch:
            return  # Safety abort

        # 2. Bypass HITL ONLY because we are sandboxed
        os.environ["BRAIN_OS_HEADLESS"] = "1"

        # 3. Token Economics Guardrail
        # We explicitly instruct the PM to limit scope so it doesn't burn $20 in one dream.
        prompt = (
            f"You are operating in a REM Sleep Dream State (Branch: {branch}). "
            f"Look at the code in Studio/{project}. Formulate ONE small, highly experimental feature or refactor. "
            f"Use the operate_forge tool to build it. "
            f"CRITICAL TOKEN ECONOMICS: Limit the Forge execution to a single focused task. Do not rewrite the whole app."
        )

        execute_pipeline(prompt, "FORGE", "STUDIO")

        console.print(
            f"\n[bold green]🌅 Host awakened. Dream safely preserved in Git branch: {branch}.[/bold green]"
        )
        console.print(
            "[dim]Use 'git diff main' in that directory to review the AI's autonomous work.[/dim]"
        )


@app.command()
def logs(
    limit: int = typer.Option(3, help="Number of recent interactions to display."),
) -> None:
    if not LOG_FILE.exists():
        console.print("[bold red]No logs found. Run a task first![/bold red]")
        return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    recent_lines = lines[-limit:]
    console.print(
        f"\n[bold green]📊 Showing last {len(recent_lines)} interactions:[/bold green]\n"
    )
    for line in recent_lines:
        data = json.loads(line)
        meta_text = f"[bold cyan]Agent:[/bold cyan] {data['agent']}\n[bold cyan]Model:[/bold cyan] {data['model']}\n[bold cyan]Time:[/bold cyan] {data['timestamp']}\n[bold cyan]Tokens:[/bold cyan] {data.get('tokens', {})}"
        console.print(
            Panel(meta_text, title="Interaction Metadata", border_style="cyan")
        )
        console.print(
            Panel(Markdown(data["response"]), title="AI Response", border_style="white")
        )
        console.print("\n" + "=" * 50 + "\n")


@app.command()
def sleep() -> None:
    """Biological Sleep Cycle: Prunes short-term JSONL logs and consolidates into long-term structured Markdown memory."""
    console.print(
        "\n[bold magenta]🧠 Initiating Biological Sleep Cycle...[/bold magenta]"
    )

    # 1. READ HIPPOCAMPUS (Short-Term Memory)
    log_path = ROOT_DIR / "logs" / "agent_interactions.jsonl"
    if not log_path.exists():
        console.print(
            "[dim]No short-term memories found in Hippocampus. Sleep skipped.[/dim]"
        )
        return

    # BIOLOGICAL INSPIRATION: Functional Segregation of Memory
    memories_by_domain: dict[str, list[dict[str, str]]] = {}

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("user_prompt") and data.get("response"):
                    domain = data.get("domain", "NONE")
                    if domain not in memories_by_domain:
                        memories_by_domain[domain] = []

                    memories_by_domain[domain].append(
                        {
                            "role": data.get("agent", "User"),
                            "prompt": data["user_prompt"][:500],  # Cap length
                            "response": data["response"][:1000],  # Cap length
                        }
                    )
            except Exception:
                continue

    if not memories_by_domain:
        console.print("[dim]No actionable memories found. Triggering Amnesia...[/dim]")
        log_path.unlink()
        return

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 2. LOAD NEOCORTEX MAP
    memory_yaml = ROOT_DIR / "System" / "config" / "memory.yaml"
    with open(memory_yaml, "r", encoding="utf-8") as f:
        domains = yaml.safe_load(f).get("domains", {})

    model = (
        "openai/gpt-4o-mini"
        if os.environ.get("OPENAI_API_KEY")
        else "anthropic/claude-3-haiku-20240307"
    )

    current_date_short = datetime.now().strftime("%Y-%m-%d")

    for domain_name, rel_path in domains.items():
        # ZERO-DEBT: Skip API calls for domains that had no activity today
        domain_logs = memories_by_domain.get(domain_name, [])
        global_logs = memories_by_domain.get("NONE", [])
        combined_logs = domain_logs + global_logs

        if not combined_logs and domain_name != "META":
            console.print(
                f"[dim]No new memories for {domain_name}. Skipping API call.[/dim]"
            )
            continue

        daily_log = json.dumps(combined_logs, indent=2)

        # --- EXPLAINABILITY: Print Expected Cost ---
        interaction_count = len(combined_logs)
        estimated_tokens = (
            len(daily_log) // 4
        )  # Standard 1 token ~ 4 chars approximation
        console.print(
            f"\n[bold blue]Processing {domain_name} Domain:[/bold blue] {interaction_count} short-term memories (~{estimated_tokens} input tokens)"
        )

        mem_file = ROOT_DIR / rel_path
        if not mem_file.exists():
            continue

        # 3. SHIFT-LEFT: Immutable Versioning (Backup before mutation)
        backup_dir = ROOT_DIR / "logs" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mem_file, backup_dir / f"{mem_file.stem}_{date_str}.md")

        current_memory = mem_file.read_text(encoding="utf-8")

        # 4. REM SLEEP: Synaptic Pruning Prompt
        system_prompt = f"""You are the Brain OS Sleep Consolidator. Your job is biological synaptic pruning.
1. Read the CURRENT NEOCORTEX MEMORY.
2. Read the DAILY HIPPOCAMPUS LOG.
3. Identify new persistent facts relevant to the '{domain_name}' domain.
4. Supersede stale facts (mark old ones as 'Superseded: [Reason]', do not blindly delete history).
5. Discard transient noise and duplicates.
6. Maintain the 100KB rule: Keep it strictly concise.
7. TIMESTAMP MANDATE: Every new memory added MUST be prefixed with today's date: [{current_date_short}].
8. NEUROPLASTICITY: If the logs reveal a critical structural error or a strict new rule an agent must obey forever, output a <neuroplasticity agent="agent_name">The rule.</neuroplasticity> block (e.g., agent="product_manager").
9. OUTPUT FORMAT: First, output a <sleep_summary>...</sleep_summary> block. Second, output any <neuroplasticity> blocks. Finally, output ONLY the updated markdown file (including the <working_memory> tags). Do not use markdown code block formatting."""

        # --- FIX: Define the payload using the current memory and the daily logs ---
        # Note: If your for-loop uses a different variable name for the logs (like 'log_text' or 'interactions'), change 'logs' to match it!
        payload = f"CURRENT NEOCORTEX MEMORY:\n{current_memory}\n\nNEW DAILY HIPPOCAMPUS LOGS:\n{logs}"

        console.print(f"[dim]Consolidating {domain_name} memory...[/dim]")
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload},
                ],
            )

            # Extract the raw text from the LLM response
            raw_content = str(response.choices[0].message.content)

            # --- EXPLAINABILITY: Extract and Print Summary ---
            summary_match = re.search(
                r"<sleep_summary>(.*?)</sleep_summary>", raw_content, re.DOTALL
            )
            if summary_match:
                summary_text = summary_match.group(1).strip()
                console.print(
                    Panel(
                        summary_text,
                        title=f"🧠 {domain_name} Consolidation Summary",
                        border_style="magenta",
                    )
                )
                new_memory = raw_content.replace(summary_match.group(0), "").strip()
            else:
                new_memory = raw_content

            # --- NEUROPLASTICITY: Guided Evolution (Staging Area) ---
            np_matches = list(
                re.finditer(
                    r'<neuroplasticity agent="(.*?)">(.*?)</neuroplasticity>',
                    new_memory,
                    re.DOTALL,
                )
            )
            if np_matches:
                mutations_path = ROOT_DIR / "Meta" / "Mutations.md"
                mutations_path.parent.mkdir(parents=True, exist_ok=True)

                with open(mutations_path, "a", encoding="utf-8") as f:
                    for match in np_matches:
                        f.write(f"\n{match.group(0)}\n")

                console.print(
                    f"[bold yellow]🧬 {len(np_matches)} new genetic mutation(s) proposed! Review Personal/Mutations.md[/bold yellow]"
                )

                for match in np_matches:
                    # Strip the XML out so it doesn't leak into the Vault Markdown
                    new_memory = new_memory.replace(match.group(0), "").strip()

            # Clean accidental markdown wrappings
            if new_memory.startswith("```markdown"):
                new_memory = new_memory[11:-3].strip()
            elif new_memory.startswith("```"):
                new_memory = new_memory[3:-3].strip()

            mem_file.write_text(new_memory, encoding="utf-8")
            console.print(
                f"✅ [green]Synaptic Pruning complete for {domain_name}.[/green]"
            )
        except Exception as e:
            console.print(f"❌ [red]Failed to consolidate {domain_name}: {e}[/red]")

    # 5. AMNESIA: Log Rotation
    archive_dir = ROOT_DIR / "logs" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    log_path.rename(archive_dir / f"hippocampus_{date_str}.jsonl")

    console.print(
        "[bold magenta]🌙 Sleep cycle complete. Hippocampus archived. OS is ready for a new day.[/bold magenta]\n"
    )


@app.command()
def evolve() -> None:
    """Cortical Inhibition: Merges approved neuroplastic mutations into the system DNA."""
    import shutil
    import yaml

    mutations_path = ROOT_DIR / "Meta" / "Mutations.md"
    agents_path = ROOT_DIR / "System" / "config" / "agents.yaml"
    backup_path = ROOT_DIR / "System" / "config" / "agents.yaml.bak"

    if not mutations_path.exists():
        console.print("[dim]No pending mutations found in Personal/Mutations.md.[/dim]")
        return

    raw_mutations = mutations_path.read_text(encoding="utf-8")
    np_matches = list(
        re.finditer(
            r'<neuroplasticity agent="(.*?)">(.*?)</neuroplasticity>',
            raw_mutations,
            re.DOTALL,
        )
    )

    if not np_matches:
        console.print(
            "[dim]No valid <neuroplasticity> tags found in staging area.[/dim]"
        )
        return

    console.print("\n[bold magenta]🧬 Initiating Guided Evolution...[/bold magenta]")

    # 1. Safety Backup
    shutil.copy2(agents_path, backup_path)
    console.print("[green]✓ Safely backed up DNA to agents.yaml.bak[/green]")

    # 2. Parse and Apply
    try:
        with open(agents_path, "r", encoding="utf-8") as yf:
            agents_data = yaml.safe_load(yf)

        applied_count = 0
        from datetime import datetime

        current_date = datetime.now().strftime("%Y-%m-%d")

        for match in np_matches:
            target_agent = match.group(1).strip()
            new_rule = match.group(2).strip()

            if target_agent in agents_data.get("agents", {}):
                agents_data["agents"][target_agent]["system_prompt"] += (
                    f'\n<neuroplastic_rule date="{current_date}">\n{new_rule}\n</neuroplastic_rule>\n'
                )
                console.print(
                    f"  [cyan]↳ Rewired {target_agent}:[/cyan] {new_rule[:50]}..."
                )
                applied_count += 1
            else:
                console.print(
                    f"  [red]↳ Unknown agent '{target_agent}'. Skipping.[/red]"
                )

        # 3. Write new DNA
        with open(agents_path, "w", encoding="utf-8") as yf:
            yaml.dump(agents_data, yf, default_flow_style=False, sort_keys=False)

        # 4. Clear Staging Area
        mutations_path.write_text("\n", encoding="utf-8")

        console.print(
            f"\n[bold green]✅ Evolution Complete. {applied_count} new traits assimilated.[/bold green]"
        )

    except Exception as e:
        console.print(f"\n[bold red]🛑 EVOLUTION FAILED: {e}[/bold red]")
        console.print("[yellow]Rolling back to backup...[/yellow]")
        shutil.copy2(backup_path, agents_path)


@app.command()
def init() -> None:
    console.print("\n[bold blue]🚀 Initializing Brain OS Vault...[/bold blue]")
    # 1. ROOT DIR IS DEFINED HERE
    root_dir = Path(__file__).parent.parent

    # We add the deep folders here so Obsidian doesn't crash looking for them
    for dir_name in [
        "Personal",
        "Personal/Scratchpad",
        "Personal/Journal",
        "Professional",
        "Professional/Projects",
        "Studio",
        "Meta",
        "Media",
        "Media/Attachments",
        "logs",
    ]:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓ Created directory:[/green] {dir_name}/")
        else:
            console.print(f"[dim]✓ Directory exists:[/dim] {dir_name}/")

    memories = {
        "Meta/global-memory.md": "# Brain OS: Global Memory\n\n<user_persona>\n- Name: User\n</user_persona>\n\n<working_memory>\n- Brain OS successfully initialized.\n</working_memory>\n",
        "Personal/personal-memory.md": "# Personal Memory\n\n<working_memory>\n</working_memory>\n",
        "Professional/professional-memory.md": "# Professional Memory\n\n<working_memory>\n</working_memory>\n",
        "Studio/studio-memory.md": "# Studio Memory\n\n<working_memory>\n</working_memory>\n",
    }
    for file_path, content in memories.items():
        full_path = root_dir / file_path
        if not full_path.exists():
            full_path.write_text(content, encoding="utf-8")
            console.print(f"[green]✓ Created file:[/green] {file_path}")
        else:
            console.print(f"[dim]✓ File exists:[/dim] {file_path}")

    env_example, env_file = root_dir / ".env.example", root_dir / ".env"
    if env_example.exists() and not env_file.exists():
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
        console.print("[green]✓ Created file:[/green] .env (Copied from template)")

    # --- 2. SHIFT-LEFT: AUTONOMOUS GIT HOOK SYNCHRONIZATION MUST GO HERE ---
    console.print("\n[bold blue]🔗 Synchronizing Repository Hooks...[/bold blue]")

    # Recursively search for any Git repositories inside the Brain OS root
    for git_dir in root_dir.rglob(".git"):
        if not git_dir.is_dir():
            continue

        repo_root = git_dir.parent
        hook_dir = repo_root / "scripts" / "githooks"

        # If the repository has a custom githooks folder (like Forge), wire it up!
        if hook_dir.exists():
            try:
                # Tell Git to use the custom folder
                subprocess.run(
                    ["git", "config", "core.hooksPath", "scripts/githooks"],
                    cwd=repo_root,
                    capture_output=True,
                    check=False,
                )

                # Force the pre-commit file to be executable (crucial for Windows/Linux interoperability)
                pre_commit_file = hook_dir / "pre-commit"
                if pre_commit_file.exists():
                    subprocess.run(
                        [
                            "git",
                            "update-index",
                            "--chmod=+x",
                            "scripts/githooks/pre-commit",
                        ],
                        cwd=repo_root,
                        capture_output=True,
                        check=False,
                    )

                console.print(
                    f"[green]✓ Secured Git hooks for repository:[/green] {repo_root.name}"
                )
            except Exception as e:
                console.print(
                    f"[dim]⚠️ Failed to wire hooks for {repo_root.name}: {e}[/dim]"
                )

    # 3. FINAL PRINT
    console.print("\n[bold green]✅ Initialization Complete![/bold green]\n")


@app.command()
def start_autonomic():
    """Wakes up the Autonomic Nervous System (Background Pacemaker)."""
    from System.organs.autonomic import run_pacemaker

    run_pacemaker()


@app.command()
def observe(
    target: str = typer.Argument(
        ...,
        help="The path to the project folder (for code) or specific file (for writing).",
    ),
    writing: bool = typer.Option(
        False,
        "--writing",
        "-w",
        help="Observe writing style instead of code style. Requires a specific file path.",
    ),
) -> None:
    """Mirror Neurons: Scans human code or prose to deduce style and proposes genetic alignment mutations."""
    from System.organs.mirror_neurons import observe_human_behavior

    os.environ["BRAIN_OS_HEADLESS"] = "1"

    # We add Studio/ automatically if it's not a writing file for backwards compatibility
    if not writing and not target.startswith("Studio/"):
        target = f"Studio/{target}"

    observe_human_behavior(target, is_writing=writing)


@app.command()
def watch(
    target: str = typer.Option(
        None,
        "--target",
        "-t",
        help="Specific directory to feel for changes. Defaults to all core domains.",
    ),
) -> None:
    """Somatosensory Cortex: Runs a background watcher to trigger local reflexes."""
    from System.organs.somatosensory import start_local_watcher

    # If a specific target is provided, wrap it in a list. Otherwise, pass None to use all defaults.
    target_list = [target] if target else None
    start_local_watcher(target_dirs=target_list)


@app.command()
def reindex() -> None:
    """Maintenance: Wipes and rebuilds the Ephemeral Glass Brain (SQLite index) from flat files."""
    reindex()


if __name__ == "__main__":
    app()
