import json
import subprocess
from pathlib import Path
from rich.console import Console
import os
import shutil
import time
from System.ast_parser import extract_signatures

# Define the absolute root of the Brain OS
ROOT_DIR: Path = Path(__file__).parent.parent.resolve()

# The AI can see everything, but can ONLY write to these specific folders
ALLOWED_DIRECTORIES: set[Path] = {
    ROOT_DIR / "Personal",
    ROOT_DIR / "Professional",
    ROOT_DIR / "Studio",
    ROOT_DIR / "Meta",
    ROOT_DIR / "Media",  # <-- The universal binary blob store
}

console = Console()


def is_safe_path(target_path: Path) -> bool:
    """Check if the target path strictly resides within allowed directories."""
    resolved_target = target_path.resolve()
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue
    return False


def write_safe_file(filepath: str, content: str) -> str:
    """Writes files safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to write at {target_path}."

        # SHIFT-LEFT SAFETY: Block any modification to Architectural Decision Records
        if "adr" in target_path.parts:
            return f"SECURITY BLOCK: Cannot modify ADRs. Human approval required for {filepath}."

        # --- 🦠 IMMUNE SYSTEM REFLEX (Secret Scanning) ---
        from System.neuroanatomy.systemic.immune_system import scan_for_pathogens

        is_clean, immune_reason = scan_for_pathogens(content)
        if not is_clean:
            return immune_reason

        # --- ⚖️ VESTIBULAR REFLEX (Take Snapshot) ---
        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(filepath)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return f"SUCCESS: File safely written to {target_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to write file - {str(e)}"


def read_safe_file(filepath: str) -> str:
    """Reads the contents of a file within the safe zones."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to read at {target_path}."
        if not target_path.exists():
            return f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
        if not target_path.is_file():
            return "ERROR: Target is not a file."

        # SHIFT-LEFT: XML Framing for Prompt Caching & Attention
        content = target_path.read_text(encoding="utf-8")
        return f'<document path="{filepath}">\n{content}\n</document>'
    except Exception as e:
        return f"ERROR: Failed to read file - {str(e)}"


def read_file_signatures(filepath: str) -> str:
    """Reads a code file and returns only its class and function signatures (AST stubs)."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()

        # 1. Ironclad Sandbox Checks
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to read at {target_path}."
        if not target_path.exists():
            return f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
        if not target_path.is_file():
            return "ERROR: Target is not a file."

        # 2. File Type Guard
        valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx"}
        if target_path.suffix not in valid_exts:
            return f"ERROR: AST stubbing currently only supports {', '.join(valid_exts)} files. Provided: {target_path.suffix}"

        # 3. AST Extraction (Using the new universal parser)
        stubs = extract_signatures(str(target_path))

        # 4. XML Framing for Prompt Caching
        return (
            f'<document_signatures path="{filepath}">\n{stubs}\n</document_signatures>'
        )

    except Exception as e:
        return f"ERROR: Failed to extract signatures - {str(e)}"


def list_safe_directory(directory_path: str) -> str:
    """Lists all files and folders inside a safe directory."""
    try:
        target_path: Path = (ROOT_DIR / directory_path).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to list directory at {target_path}."
        if not target_path.exists() or not target_path.is_dir():
            return f"ERROR: Directory not found at {target_path.relative_to(ROOT_DIR)}"

        items = []
        for item in target_path.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"ERROR: Failed to list directory - {str(e)}"


def rename_safe_file(old_filepath: str, new_filepath: str) -> str:
    """Renames or moves a file within the safe zones."""
    try:
        old_path: Path = (ROOT_DIR / old_filepath).resolve()
        new_path: Path = (ROOT_DIR / new_filepath).resolve()

        if not is_safe_path(old_path) or not is_safe_path(new_path):
            return "SECURITY BLOCK: Access denied. Source and dest must be safe."

        # SHIFT-LEFT SAFETY: Check both source and destination to prevent ADR tampering/creation.
        # This MUST happen before checking file existence to ensure absolute blocking.
        if "adr" in old_path.parts or "adr" in new_path.parts:
            return "SECURITY BLOCK: Cannot modify, move, or create ADRs. Human approval required."

        if not old_path.exists():
            return f"ERROR: File not found at {old_path.relative_to(ROOT_DIR)}"

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        return f"SUCCESS: Renamed to {new_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to rename file - {str(e)}"


def append_safe_file(filepath: str, content: str) -> str:
    """Appends content to a file safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to append at {target_path}."

        # SHIFT-LEFT SAFETY: Block any modification to Architectural Decision Records
        if "adr" in target_path.parts:
            return f"SECURITY BLOCK: Cannot modify ADRs. Human approval required for {filepath}."

        # --- 🦠 IMMUNE SYSTEM REFLEX (Secret Scanning) ---
        from System.neuroanatomy.systemic.immune_system import scan_for_pathogens

        is_clean, immune_reason = scan_for_pathogens(content)
        if not is_clean:
            return immune_reason

        # --- ⚖️ VESTIBULAR REFLEX (Take Snapshot) ---
        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(filepath)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = ""
        if target_path.exists():
            with open(target_path, encoding="utf-8") as f:
                current_content = f.read()
                if current_content and not current_content.endswith("\n"):
                    prefix = "\n"

        with open(target_path, "a", encoding="utf-8") as f:
            f.write(prefix + content + "\n")
        return f"SUCCESS: Appended to {target_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to append to file - {str(e)}"


def bootstrap_project(
    project_name: str, template_url: str = "https://github.com/mrdanielcasper/forge.git"
) -> str:
    """Clones a project archetype into the Studio directory and initializes dependencies."""
    try:
        target_path: Path = (ROOT_DIR / "Studio" / project_name).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to clone into {target_path}."
        if target_path.exists():
            return f"ERROR: Directory exists at {target_path.relative_to(ROOT_DIR)}"

        # 1. Clone the Repo
        result = subprocess.run(
            ["git", "clone", template_url, str(target_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # 2. Rename Remote
            subprocess.run(
                ["git", "remote", "rename", "origin", "upstream"], cwd=str(target_path)
            )

            # 3. Setup Env
            env_example = target_path / ".env.example"
            env_target = target_path / ".env"
            if env_example.exists() and not env_target.exists():
                env_target.write_text(
                    env_example.read_text(encoding="utf-8"), encoding="utf-8"
                )

            # --- SHIFT-LEFT DEVEX: Auto-Hydrate Dependencies ---
            console.print(f"[dim]Hydrating dependencies for {project_name}...[/dim]")

            # Resolve cross-platform paths safely
            npm_path = shutil.which("npm")
            uv_path = shutil.which("uv")

            if uv_path:
                subprocess.run(
                    [uv_path, "sync"], cwd=str(target_path), capture_output=True
                )
            if npm_path:
                subprocess.run(
                    [npm_path, "install"], cwd=str(target_path), capture_output=True
                )

            return f"SUCCESS: Bootstrapped and hydrated at {target_path.relative_to(ROOT_DIR)}"

        return f"ERROR: Git clone failed - {result.stderr}"
    except Exception as e:
        return f"ERROR: Failed to bootstrap project - {str(e)}"


def execute_command(command: str, directory_path: str) -> str:
    """Runs a terminal command strictly within the BBB Sandbox and demands Human Approval."""
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.limbic.amygdala import scan_command
    import subprocess
    import os
    import shlex
    from rich.console import Console

    console = Console()

    # 1. SHIFT-LEFT: Sandbox Enforcement
    is_safe_path, path_result = validate_execution_path(directory_path)
    if not is_safe_path:
        return f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>"

    # 2. SHIFT-LEFT: Semantic Intent Check
    is_safe_command, command_result = scan_command(command)
    if not is_safe_command:
        return f"<shell_output>\n<stderr>\n{command_result}\n</stderr>\n</shell_output>"

    # 3. SHIFT-LEFT: AST MEMBRANE & BINARY WHITELIST (Payload inspection)
    try:
        from System.neuroanatomy.systemic.blood_brain_barrier import scan_python_ast

        args = shlex.split(command)
        if args:
            binary = args[0].lower()

            # We only allow the agent to autonomously execute Python or Node scripts.
            # Executing 'bash' or 'sh' directly bypasses our membrane.
            if binary in ["bash", "sh", "zsh", "powershell", "pwsh", "cmd"]:
                return "<shell_output>\n<stderr>\nSECURITY BLOCK: Executing raw shell binaries is forbidden. Write Python scripts instead.\n</stderr>\n</shell_output>"

            if binary in ["python", "python3", "py"]:
                # Catch inline execution: python -c "import os..."
                if "-c" in args:
                    c_index = args.index("-c")
                    if len(args) > c_index + 1:
                        inline_code = args[c_index + 1]
                        from System.neuroanatomy.systemic.blood_brain_barrier import (
                            scan_python_ast_string,
                        )

                        is_safe_ast, ast_reason = scan_python_ast_string(inline_code)
                        if not is_safe_ast:
                            return f"<shell_output>\n<stderr>\n{ast_reason}\n</stderr>\n</shell_output>"

                # Catch file execution: python script.py
                for arg in args[1:]:
                    if arg.endswith(".py"):
                        script_path = os.path.join(path_result, arg)
                        is_safe_ast, ast_reason = scan_python_ast(script_path)
                        if not is_safe_ast:
                            return f"<shell_output>\n<stderr>\n{ast_reason}\n</stderr>\n</shell_output>"
    except ValueError:
        pass  # shlex parsing error will be caught later

    # 4. HITL Check
    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        console.print(
            f"\n[bold yellow]⚠️ Agent wants to execute command in {path_result}:[/bold yellow]"
        )
        console.print(f"[cyan]{command}[/cyan]")
        try:
            auth = input("Allow execution? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            auth = "n"

        if auth not in ["y", "yes"]:
            return "<shell_output>\n<stderr>\nSECURITY BLOCK: User explicitly denied command execution.\n</stderr>\n</shell_output>"

    # 4. Execution (SECURED: shell=False + shlex)
    try:
        # Safely parse the command string into an array to prevent RCE injection
        args = shlex.split(command)
        result = subprocess.run(
            args,
            shell=False,
            cwd=path_result,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # RESTORED AND CORRECTED: Microglia Autonomous Bug Fixing
        if result.returncode != 0:
            from System.neuroanatomy.systemic.microglia import trigger_immune_response

            # The Microglia intercepts the failure, generates an antibody patch,
            # and applies it autonomously in the correct directory.
            trigger_immune_response(command, result.stderr, path_result)

        # RESTORED: XML Data Contract
        return f"<shell_output>\n<stdout>\n{result.stdout}\n</stdout>\n<stderr>\n{result.stderr}\n</stderr>\n</shell_output>"
    except subprocess.TimeoutExpired:
        return "<shell_output>\n<stderr>\nERROR: Command timed out after 60 seconds.\n</stderr>\n</shell_output>"
    except Exception as e:
        return f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>"


def operate_forge(project_name: str, instruction: str) -> str:
    """Operates a Forge instance securely via handoff.md and returns its telemetry."""
    try:
        target_path: Path = (ROOT_DIR / "Studio" / project_name).resolve()

        # 1. SHIFT-LEFT SAFETY: Path Traversal & Sandbox Check
        if not is_safe_path(target_path):
            return (
                f"SECURITY BLOCK: Access denied. {target_path} is outside safe zones."
            )

        orchestrator_path = target_path / "orchestrator.py"
        if not orchestrator_path.exists():
            return f"ERROR: Forge engine not found at {orchestrator_path.relative_to(ROOT_DIR)}."

        # 2. STATE PREPARATION: Write the instruction deterministically
        ops_dir = target_path / "docs" / "ops"
        ops_dir.mkdir(parents=True, exist_ok=True)
        handoff_path = ops_dir / "handoff.md"
        handoff_path.write_text(f"PROMPT: {instruction}\n", encoding="utf-8")

        # 3. SHIFT-LEFT SAFETY: Human-in-the-Loop Authorization
        console.print(
            "\n[bold red]⚠️  SECURITY ALERT: FORGE OPERATION REQUESTED[/bold red]"
        )
        console.print(
            f"[yellow]Brain OS wants to command Forge for project:[/yellow] '{project_name}'\n"
            f"[yellow]Instruction:[/yellow] '{instruction}'"
        )

        # --- SHIFT-LEFT: STRICT Opt-In Gate ---
        if os.environ.get("BRAIN_OS_HEADLESS") == "1":
            user_input = "y"
        else:
            try:
                user_input = input("Allow execution? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                user_input = "n"

        if user_input not in ["y", "yes"]:
            return "SECURITY BLOCK: User explicitly denied Forge operation."

        console.print(f"[dim]Booting Forge engine for '{project_name}'...[/dim]\n")

        # 4. EXECUTION: shell=False completely eliminates shell injection vectors
        result = subprocess.run(
            ["uv", "run", "orchestrator.py"],
            cwd=str(target_path),
        )

        # 5. OBSERVABILITY: Harvest Telemetry & Status
        telemetry_path = ops_dir / "telemetry.jsonl"
        telemetry_data = "No telemetry emitted."
        if telemetry_path.exists():
            with open(telemetry_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    try:
                        t_json = json.loads(lines[-1])
                        telemetry_data = f"Last Agent: {t_json.get('agent')} | Tokens: {t_json.get('prompt_tokens')} | Latency: {t_json.get('latency_s')}s"
                    except json.JSONDecodeError:
                        telemetry_data = "Telemetry parsing failed."

        handoff_status = (
            handoff_path.read_text(encoding="utf-8").strip()
            if handoff_path.exists()
            else "No state."
        )

        # 6. RETURN: Highly structured data for the Brain OS LLM
        summary = (
            f"FORGE EXECUTION COMPLETE (Exit Code {result.returncode})\n\n"
            f"--- TELEMETRY ---\n{telemetry_data}\n\n"
            f"--- HANDOFF STATE ---\n{handoff_status}\n\n"
            f"--- ENGINE STDOUT ---\n(Streamed live to user terminal. Rely on Telemetry and Handoff State above.)\n"
        )

        if result.returncode != 0:
            summary += "\n--- ERROR ---\nForge execution failed. Please check the live terminal output for the exact stack trace."

        return summary

    except Exception as e:
        return f"ERROR: Failed to operate Forge - {str(e)}"


def copy_safe_file(source_filepath: str, dest_filepath: str) -> str:
    """Copies a file from one safe location to another."""
    try:
        source_path: Path = (ROOT_DIR / source_filepath).resolve()
        dest_path: Path = (ROOT_DIR / dest_filepath).resolve()

        if not is_safe_path(source_path) or not is_safe_path(dest_path):
            return "SECURITY BLOCK: Access denied. Source and dest must be safe."
        if not source_path.exists():
            return (
                f"ERROR: Source file not found at {source_path.relative_to(ROOT_DIR)}"
            )

        # SHIFT-LEFT SAFETY: Protect ADRs
        if "adr" in source_path.parts or "adr" in dest_path.parts:
            return "SECURITY BLOCK: Cannot copy ADRs."

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        return f"SUCCESS: Copied to {dest_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to copy file - {str(e)}"


def search_safe_directory(query: str, directory_path: str) -> str:
    """Recursively searches for a string within safe directory bounds, returning telemetry."""
    start_time = time.perf_counter()
    target_path = (ROOT_DIR / directory_path).resolve()

    # SHIFT-LEFT SECURITY: Always check authorization BEFORE existence
    # to prevent path enumeration attacks.
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot search outside allowed directories. Attempted to access {target_path}"

    if not target_path.exists():
        return f"ERROR: Directory '{directory_path}' does not exist."

    results = []
    files_scanned = 0
    # ... (the rest of the function remains exactly the same)
    # Ignore binary, cache, and massive dependency folders
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
    valid_exts = {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".css",
        ".html",
        ".txt",
    }

    try:
        for filepath in target_path.rglob("*"):
            if filepath.is_file() and filepath.suffix in valid_exts:
                if any(ignored in filepath.parts for ignored in ignore_dirs):
                    continue

                files_scanned += 1
                content = filepath.read_text(errors="ignore")
                if query.lower() in content.lower():
                    results.append(f"- {filepath.relative_to(ROOT_DIR)}")

                    # Prevent LLM context bloat
                    if len(results) >= 15:
                        results.append(
                            "... (Additional results truncated for token limits)"
                        )
                        break

    except Exception as e:
        return f"ERROR: Failed to search directory - {str(e)}"

    duration = time.perf_counter() - start_time
    telemetry = f"[Telemetry: Scanned {files_scanned} files in {duration:.3f} seconds]"

    if not results:
        return f"No matches found for '{query}' in {directory_path}. {telemetry}"

    return (
        f"Found '{query}' in the following files:\n"
        + "\n".join(results)
        + f"\n\n{telemetry}"
    )


def analyze_safe_syntax(filepath: str) -> str:
    """Runs a read-only local linter against a file to check for syntax errors."""
    target_path = (ROOT_DIR / filepath).resolve()

    # SHIFT-LEFT SECURITY: Always check authorization BEFORE existence
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot lint outside allowed directories. Attempted to access {target_path}"

    if not target_path.exists():
        return f"ERROR: File '{filepath}' does not exist."

    # Only lint supported file types
    if target_path.suffix == ".py":
        try:
            # Run ruff check without modifying the file (--no-cache to avoid ghost state)
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "--no-cache", str(target_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return f"✅ Linter passed for {filepath}. No syntax errors found."
            else:
                return f"❌ Linter found errors in {filepath}:\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"ERROR: Failed to run linter subprocess. Details: {e}"
    else:
        return f"WARNING: Syntax analysis for {target_path.suffix} files is not yet implemented. Only .py files are currently supported."


def sense_environment(url: str) -> str:
    """
    Uses the independent Sense organ to fetch and read an external webpage.
    Returns highly-optimized Hybrid XML/MD.
    """
    try:
        # UNIX PHILOSOPHY: Call the external organ via stdout/stderr piping
        result = subprocess.run(
            ["uv", "run", "sense", url], capture_output=True, text=True, check=False
        )

        # If Sense blocked the request (e.g., SSRF) or crashed
        if result.returncode != 0:
            return f'<sensory_error source="{url}">\nSense Error: {result.stdout.strip()}\n{result.stderr.strip()}\n</sensory_error>'

        # The success output is already formatted as <sensory_input> by the CLI
        return result.stdout.strip()

    except Exception as e:
        return f'<sensory_error source="{url}">\nFailed to invoke Sense organ: {str(e)}\n</sensory_error>'


def create_engram_tool(name: str, description: str, commands: str) -> str:
    """
    Saves a sequence of bash/shell commands into procedural muscle memory.
    Use this when you successfully complete a complex, multi-step task that will likely be repeated.
    """
    from System.neuroanatomy.autonomic.cerebellum import save_engram

    return save_engram(name, description, commands)


def list_engrams_tool() -> str:
    """Lists all available muscle memory scripts (engrams) the system knows how to do instantly."""
    from System.neuroanatomy.autonomic.cerebellum import list_engrams

    return list_engrams()


def execute_engram_tool(name: str, args: str = "") -> str:
    """
    Instantly executes a learned engram (bash script).
    Use this instead of manually executing shell commands if an engram already exists.
    """
    from System.neuroanatomy.autonomic.cerebellum import execute_engram

    return execute_engram(name, args)


def search_hippocampus(query: str) -> str:
    """Searches the AI's long-term ephemeral index for code snippets."""
    from System.neuroanatomy.limbic.hippocampus import recall_memory

    return recall_memory(query)


def manage_background_process(
    action: str, name: str = "", command: str = "", cwd: str = ""
) -> str:
    """
    Proprioception Motor Control: Start, stop, or list background processes (like local dev servers).

    Parameters:
    - action: Must be 'start', 'stop', or 'list'.
    - name: A unique identifier for the process (e.g., 'frontend_server'). Required for start/stop.
    - command: The terminal command to run (e.g., 'npm run dev'). Required for 'start'.
    - cwd: The directory to run the command in (optional).
    """
    from System.neuroanatomy.autonomic.proprioception import (
        start_process,
        stop_process,
        list_processes,
    )

    if action == "list":
        return list_processes()
    elif action == "start":
        if not name or not command:
            return "Error: Both 'name' and 'command' are required to start a process."
        return start_process(name, command, cwd if cwd else None)
    elif action == "stop":
        if not name:
            return "Error: 'name' is required to stop a process."
        return stop_process(name)
    else:
        return "Error: Invalid action. Must be 'start', 'stop', or 'list'."


def analyze_image(image_path: str, query: str) -> str:
    """
    Use this to look at and analyze an image file on the disk (e.g., a screenshot or diagram).
    Pass a specific query like 'Does this UI match the spec?' or 'What is in this image?'.
    """
    from System.neuroanatomy.cortical.occipital import perceive_image

    return perceive_image(image_path, query)


def generate_image(prompt: str, output_filename: str) -> str:
    """
    Generates a visual asset (PNG/JPG) using an AI image generator based on your text prompt.
    The image will be saved to the Studio/ directory.
    output_filename should be a relative path like 'My-App/public/logo.png'.
    """
    from System.neuroanatomy.cortical.occipital import generate_visual_asset

    return generate_visual_asset(prompt, output_filename)


def capture_screenshot(url: str) -> str:
    """Takes a headless screenshot and explicitly quarantines it in the Meta/Visual_Cortex buffer."""
    from Sense.receptors.vision import take_screenshot
    from pathlib import Path

    # Force the screenshot into a quarantined OS buffer
    visual_cortex_dir = Path(__file__).parent.parent / "Meta" / "Visual_Cortex"
    visual_cortex_dir.mkdir(parents=True, exist_ok=True)

    output_path = visual_cortex_dir / "latest_screenshot.png"

    # Call the receptor
    take_screenshot(url, str(output_path))
    return f"Screenshot successfully captured and saved to {output_path.as_posix()}"


def semantic_search(directory: str, query: str) -> str:
    """
    A deep semantic search. Uses keyword search to grab a broad batch of notes,
    and then uses Wernicke's Area (an LLM) to comprehend and extract the exact answer.
    """
    from System.tools import search_safe_directory
    from System.neuroanatomy.cortical.wernicke import filter_semantic_relevance

    # 1. Fast Path (Hippocampus): Get keyword matches
    # Removed the invalid 'limit' arg and explicitly named the parameters
    raw_results = search_safe_directory(query=query, directory_path=directory)

    # 2. Comprehension Path (Wernicke): Filter out the noise
    semantic_result = filter_semantic_relevance(query, raw_results)

    return semantic_result


def speak(text: str) -> str:
    """BROCA + MOUTH: Speaks text out loud to the user."""
    from System.neuroanatomy.cortical.broca import synthesize_speech
    from Sense.receptors.audio import play_audio
    import tempfile
    from pathlib import Path

    try:
        out_file = Path(tempfile.gettempdir()) / "brain_tool_speech.mp3"
        synthesize_speech(text, str(out_file))
        play_audio(str(out_file))
        return "SUCCESS: Text spoken out loud to the user."
    except Exception as e:
        return f"SPEECH ERROR: {str(e)}"


def analyze_audio(filepath: str) -> str:
    """TEMPORAL LOBE + WERNICKE: Transcribes speech and analyzes environmental sound."""
    from System.neuroanatomy.cortical.wernicke import transcribe_speech
    from System.neuroanatomy.cortical.temporal_lobe import comprehend_sound

    try:
        target_path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return "SECURITY BLOCK: Cannot access audio files outside the sandbox."

        if not target_path.exists():
            return f"ERROR: File {filepath} does not exist."

        speech = transcribe_speech(str(target_path))
        environment = comprehend_sound(str(target_path))

        return (
            f"<auditory_analysis>\n"
            f"  <speech>\n{speech}\n  </speech>\n"
            f"  <environment>\n{environment}\n  </environment>\n"
            f"</auditory_analysis>"
        )
    except Exception as e:
        return f"AUDIO ANALYSIS ERROR: {str(e)}"


def delete_safe_file(filepath: str) -> str:
    """
    LYSOSOME: Safely removes a file by moving it to a local .trash directory.
    Maintains a manifest for Human-in-the-Loop recovery.
    """
    import shutil
    import json
    from datetime import datetime

    try:
        target_path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path):
            return (
                f"SECURITY BLOCK: Cannot delete files outside the sandbox ({filepath})."
            )

        if not target_path.exists():
            return f"ERROR: File {filepath} does not exist."

        if not target_path.is_file():
            return "ERROR: delete_safe_file only works on files, not directories."

        # The Trash Membrane
        trash_dir = ROOT_DIR / ".trash"
        trash_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_trash_name = f"{target_path.stem}_{timestamp}{target_path.suffix}"
        trash_path = trash_dir / safe_trash_name

        # Move the file
        shutil.move(str(target_path), str(trash_path))

        # Log the recovery data
        manifest_path = trash_dir / "manifest.jsonl"
        recovery_data = {
            "deleted_at": timestamp,
            "original_path": str(target_path.relative_to(ROOT_DIR)),
            "trash_path": str(trash_path.relative_to(ROOT_DIR)),
        }
        with open(manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(recovery_data) + "\n")

        return f"SUCCESS: File safely moved to {trash_path.relative_to(ROOT_DIR)}. (Logged in manifest)."

    except Exception as e:
        return f"DELETE ERROR: {str(e)}"


def taste_safe_file(filepath: str) -> str:
    """
    GUSTATORY: Safely samples large/dense files (PDF, CSV, Logs) to prevent token bloat.
    """
    from System.neuroanatomy.sensory.gustatory import process_taste_profile

    target_path = (ROOT_DIR / filepath).resolve()
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot taste files outside the sandbox ({filepath})."

    return process_taste_profile(filepath)


def map_spatial_dependencies(
    directory_path: str, output_format: str = "json", map_type: str = "code"
) -> str:
    """
    PARIETAL LOBE: Generates a spatial dependency graph.
    Formats: 'json', 'mermaid', 'vertigo_check'.
    Map Types: 'code' (imports) or 'notes' (Obsidian links).
    """
    from System.neuroanatomy.cortical.parietal_lobe import generate_spatial_map

    target_path = (ROOT_DIR / directory_path).resolve()
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot map dependencies outside the workspace ({directory_path})."

    return generate_spatial_map(str(target_path), output_format, map_type)
