# 🛡️ Brain - Security Architecture & Threat Model

Most autonomous multi-agent frameworks are highly vulnerable to prompt injections, remote code execution (RCE) loops, path traversals, and secret disclosures because they treat the agent execution environment as a trusted shell.

Brain **attempts** to solve this by enforcing **Shift-Left Perimeter Defense-in-Depth**. The architecture assumes that sub-agents *will* encounter malicious inputs and tokenized exploits. Instead of relying on fragile prompt engineering boundaries, the system stacks static code analysis, real-time syscall interception, out-of-process process supervision, and OS kernel jailing to completely isolate the execution runtime.

---
## 🎯 Summary of Developer Protection Controls

| Security Vector          | Risk Prevented                                                     | Underlying Implementation Subsystem                                                                                      |
| ------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **Command Injection**    | Unauthorized software installations, untrusted network fetching.   | **Blood-Brain Barrier**: Static command filtering and regex matching patterns inside `blood_brain_barrier.py`.           |
| **Malicious Scripts**    | Dangerous system manipulation or dynamic evaluation workarounds.   | **AST Membrane 2.0**: Abstract Syntax Tree module node inspection and obfuscation check flags.                           |
| **File Destruction**     | Arbitrary deletions, path traversal, or out-of-bounds writing.     | **Cellular Apoptosis**: PEP 578 Runtime Audit Hooks and write-vector path checks inside `sys.addaudithook`.              |
| **Resource Depletion**   | Fork bombs, memory leakage, or infinite resource thrashing.        | **Kernel Jailing**: Win32 Job Objects and POSIX resource allocations (`rlimit`) mapped directly at the kernel scheduler. |
| **Credential Leakage**   | Exposing API credentials to sub-agents, logs, or terminal views.   | **SecretVault + Macrophages**: Memory scrubbing and outbound regex-matched data filtering.                               |
| **Rogue Agent Takeover** | Runaway processes writing unvetted configuration code recursively. | **Thymus Watchdog**: Out-of-process IPC polling, rolling velocity mathematics, and forced `SIGKILL` isolation.           |

---
## 🧭 The Ingress-to-Kernel Processing Chain

When an untrusted payload or tool execution request enters the environment, it travels through six distinct validation barriers before interacting with the host system:

```text
    [Inbound Stimulus / Untrusted Task Payload]
                       │
                       ▼
         ┌──────────────────────────┐
         │ 1. Polymorphic Sensor    │  <-- Token Encapsulation & Cleansing
         └───────────┬──────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │ 2. Blood-Brain Barrier   │  <-- Headless Mode Network Firewall
         └───────────┬──────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │ 3. AST Membrane 2.0      │  <-- Ahead-of-Time Syntax Tree Audit
         └───────────┬──────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │ 4. Cellular Apoptosis    │  <-- Low-Level Runtime Audit Hook Isolation
         └───────────┬──────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │ 5. Endogenous Immunity   │  <-- Environment & Data Stream Scrubbing
         └───────────┬──────────────┘
                     │
                     ▼
  =====================▼======================================================
  🧠 LEVEL 0: THE GUARDIAN MEMBRANE (Kernel & Process Supervision)
  ==========================================================================
                     │
                     ▼
         ┌──────────────────────────┐
         │ 6a. OS Sandbox Jailing   │  <-- Win32 Job Objects / POSIX rlimit
         └───────────┬──────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │ 6b. Thymus Gland Monitor │  <-- Out-of-Process Parent Watchdog
         └──────────────────────────┘

```

---
## 🛠️ Architectural Breakdown of the 6 Defensive Layers

### 1. Polymorphic Sensor Armor & Path Validation

* **Source Subsystem:** `System/neuroanatomy/systemic/blood_brain_barrier.py`
* **Primary Targets:** `scrub_payload()`, `validate_execution_path()`
* **Threats Mitigated:** Prompt Injection Attacks, Markdown Block Spoofing, Path Traversal Escapes.

#### Mechanics

Every external text stimulus (such as untrusted web content, raw tool inputs, or git commit records) is run through a structural sanitizer loop. The module replaces raw markdown backticks (`````) with inert code notation markers (`'''`) and wraps the string inside an explicit read-only sensory block context:

```text
[[UNVERIFIED SENSORY STIMULUS]]
...
[[END SENSORY INPUT]]

```

This layout prevents the core language model from parsing raw data text streams as active system commands.

Concurrently, directory paths are resolved using strict relative mapping against the system root. If a sub-process requests an out-of-bounds traversal (`../`), execution halts with an access violation block, restricting file manipulation to explicitly whitelisted safe sandboxes (`Studio`, `Personal`, `Professional`, `Media`).

---
### 2. The Blood-Brain Barrier (BBB)

* **Source Subsystem:** `System/neuroanatomy/systemic/blood_brain_barrier.py`
* **Primary Targets:** `inspect_toxins()`
* **Threats Mitigated:** Headless Dependency Hijacking, Supply-Chain Attacks, Remote Script Ingestion.

#### Mechanics

When Brain OS transitions into automated background tasks, headless modes, or sleep cycles, the global environment latches `BRAIN_OS_HEADLESS = "1"`. In this state, a high-specificity regex firewall inspects all upcoming shell operations.

It intercepts and kills any commands attempting package management installation (`npm install`, `pip install`, `uv add`, `yarn add`, `pnpm add`, `brew install`, `apt-get install`). It also blocks remote code streaming patterns (such as `curl ... | bash` or `wget ... | sh`), dropping the request before it can access the network stack.

---
### 3. The AST Membrane 2.0

* **Source Subsystem:** `System/neuroanatomy/systemic/blood_brain_barrier.py`
* **Primary Targets:** `scan_python_ast()`, `scan_python_ast_string()`, `ToxinDetector(ast.NodeVisitor)`
* **Threats Mitigated:** Arbitrary Code Execution, Obfuscated Module Imports, Reflective Namespace Traversal.

#### Mechanics

Before any sub-agent generated Python script or raw `-c` shell string is passed to a compiler, the file content is unpacked into an abstract syntax node tree. The `ToxinDetector` inspects every code block ahead-of-time:

* **Import Restrictions:** The module blocks any code linking to low-level operating system handles (`os`, `subprocess`, `sys`, `pty`, `shutil`, `socket`, `urllib`, `requests`).
* **Obfuscation Detection:** The analyzer checks syntax patterns to look for runtime evaluation overrides, automatically blocking the use of execution primitives like `eval`, `exec`, `__import__`, and `compile`. It also blocks access to reflection helpers like `getattr` and `setattr` to prevent internal workarounds, such as hiding malicious calls inside patterns like `getattr(os, 'system')`.

---
### 4. Cellular Apoptosis

* **Source Subsystem:** `System/neuroanatomy/systemic/blood_brain_barrier.py`
* **Primary Targets:** `wrap_with_apoptosis()`, `sys.addaudithook()`
* **Threats Mitigated:** Dynamic/Runtime Bypass Exploits, Unauthorized Sockets, Destructive Out-of-Bounds File Overwrites.

#### Mechanics

When executing complex tasks, scripts are wrapped inside a runtime membrane file via `runpy`. This membrane registers native **PEP 578 Runtime Audit Hooks** (`sys.addaudithook`) directly into the active Python engine.

If the running thread triggers a low-level syscall event (`os.system`, `subprocess.Popen`, `os.posix_spawn`, `socket.connect`, `urllib.Request`, or destructive actions like `os.remove`, `os.unlink`, `os.rmdir`, `os.rename`), the hook catches the operation and immediately drops the process via `sys.exit(1)`.

The audit hook also monitors the `"open"` syscall. If a process requests write (`w`), append (`a`), or update (`+`) access to a file, the handler verifies the target path. If the file path lands outside authorized directories (`Studio`, `Personal`, `Professional`, `Media`, `Meta`, `.trash`, `System/logs`), the audit hook intercepts the request and terminates execution.

---
### 5. Secret Vault Isolation & Endogenous Data Filtering

* **Source Subsystem:** `System/neuroanatomy/systemic/immune_system.py`
* **Primary Targets:** `SecretVault` (vault), `scan_for_pathogens()`, `mask_secrets()`
* **Threats Mitigated:** Environment Snipping, Plaintext Token Leakage, Malicious Credential Extraction.

#### Mechanics

During the system boot phase, the `SecretVault` singleton executes environment scrubbing. It fetches all sensitive API credentials (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `DEPLOYMENT_TOKEN`) from the shell configuration, maps them into an isolated, local dictionary memory structure, and **completely deletes the records from the environment variables** (`del os.environ[key]`). This ensures that external sub-processes or compromised scripts executed by sub-agents can never access LLM credentials via generic environment lookups like `os.environ`.

Outbound text streams are concurrently filtered using high-specificity regex signatures to intercept cleartext tokens (including AWS Access Keys, OpenAI project keys, Stripe secret signatures, GitHub tokens, and raw RSA/OPENSSH private key headers). If a credential is flag-matched, write access drops with an enforcement warning. To protect operational privacy, any terminal output, error message, or logging block is cross-referenced against the vault's internal dictionary, redacting them in real time (`mask_secrets()`).

---
### 6. Level 0: Hard OS-Level Resource Jailing & Out-of-Process Watchdog

At Level 0, the AI does not run as a privileged root master thread; it executes inside an isolated, resource-capped sandbox watched by an independent parent process.

#### Out-of-Process Parent Supervision (`System/neuroanatomy/systemic/thymus.py`)

The **Thymus Gland** functions as an out-of-process system supervisor. It handles initial system instantiation, spawning the core orchestration framework (`Medulla`) as a distinct child process thread.

```text
               ┌──────────────┐
               │ Thymus Gland │ <-- Out-of-process watchdog
               └──────┬───────┘
                      │ Secure, collision-free IPC
                      │ (UUID Named Pipe / UNIX Socket)
                      ▼
               ┌──────────────┐
               │   Medulla    │ <-- Running within OS-level Jail
               └──────────────┘

```

* **Collision-Free Inter-Process Communication (IPC):** The Thymus generates an ephemeral, unique 128-bit routing handle (`uuid.uuid4().hex`) at boot. It uses this token to bind a native secure channel—either a local named pipe (`\\.\pipe\brain_thymus_...`) under Windows architectures or a localized UNIX socket domain descriptor inside `tempfile.gettempdir()` on POSIX operating systems. This approach seals communication lines, preventing rogue local processes from spoofing or tapping into core orchestrator signals.
* **Defensive Non-Blocking Polling:** The supervisor uses a dedicated `_monitor_loop` that continuously checks child lifecycle states via non-blocking queries (`conn.poll(timeout=1.0)`). This design prevents deadlock conditions, ensuring the watchdog remains responsive and can immediately execute safety overrides even if the child process hangs.
* **The Velocity Tracker & State Rollback:** The Thymus tracks child operations, logging telemetry signals sent across the local IPC channel. Destructive mutations append to a rolling 10-second evaluation window (`WINDOW_SECONDS = 10`). If the count of destructive actions breaches the maximum mutation threshold (`MAX_MUTATIONS = 5`), the supervisor flags a rogue velocity exception and triggers an emergency containment protocol (`_escalate`), gracefully halting or forcefully killing (`SIGKILL`) the child process and rolling back system dependencies to their last known stable states (`vestibular.restore_balance()`).

#### Native OS Kernel Jailing (`System/tools/execution/OS/`)

To prevent an agent from spawning infinite child sub-processes or causing a system-wide out-of-memory crash, Level 0 interfaces directly with native operating system kernel resource controllers:

* **Win32 Kernel Object Constraints (`win32_jail.py`):** Under Windows, the system uses `ctypes` to declare native API structures and instantiate an isolated Windows Job Object (`kernel32.CreateJobObjectW`). It maps process limitations directly through the Windows kernel scheduler flags:
* `JOB_OBJECT_LIMIT_ACTIVE_PROCESS`: Locks the active process count to a maximum ceiling of 50 to prevent fork-bomb expansion.
* `JOB_OBJECT_LIMIT_JOB_MEMORY`: Restricts cumulative job memory usage to a hard 512MB RAM ceiling (`JobMemoryLimit = 512 * 1024 * 1024`). If a process breaches this limit, the Windows kernel triggers an out-of-memory kill event.
* `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`: Guarantees that if the master supervisor handle drops or terminates, the Windows kernel automatically sweeps and closes all orphaned child process trees.


* **POSIX Native Constraints (`posix_jail.py`):** On Linux and macOS, the system establishes a new process session via `os.setsid()` and configures resource allocations through `resource.setrlimit`. It maps process limitations through `resource.RLIMIT_NPROC`, locking maximum available thread forks to 50 to prevent resource exhaustion attacks.

---
