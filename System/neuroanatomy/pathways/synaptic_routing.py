import re
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def configure_synaptic_routing(
    project_name: str, backend_port: int, api_prefix: str = "/api"
) -> str:
    """Autonomously injects a CORS proxy into a Vite configuration file."""
    target_dir = ROOT_DIR / "Studio" / project_name

    if not target_dir.exists():
        return f"Error: Project directory {project_name} not found."

    vite_files = list(target_dir.glob("vite.config.ts")) + list(
        target_dir.glob("vite.config.js")
    )

    if not vite_files:
        return "Error: No vite.config.js or vite.config.ts found. Ensure Vite is initialized first."

    vite_file = vite_files[0]
    content = vite_file.read_text(encoding="utf-8")

    # Check if proxy already exists to prevent duplication
    if "proxy:" in content or "proxy :" in content:
        console.print(
            f"[dim yellow]🧠 Synaptic Routing: Proxy already detected in {vite_file.name}.[/dim yellow]"
        )
        return "Synaptic routing already established. Proxy detected in Vite config."

    # ⚡ SHIFT-LEFT: The Proxy Payload
    proxy_config = f"""
    proxy: {{
      '{api_prefix}': {{
        target: 'http://localhost:{backend_port}',
        changeOrigin: true,
        secure: false,
      }}
    }}"""

    # Inject into existing server block if it exists
    if "server:" in content or "server :" in content:
        content = re.sub(
            r"server\s*:\s*\{", f"server: {{{proxy_config},", content, count=1
        )
    else:
        # Otherwise, inject the server block directly inside defineConfig
        server_block = f"""
  server: {{{proxy_config}
  }},"""
        content = re.sub(
            r"defineConfig\s*\(\s*\{",
            f"defineConfig({{{server_block}",
            content,
            count=1,
        )

    vite_file.write_text(content, encoding="utf-8")
    console.print(
        f"[bold magenta]🧠 Synaptic Routing Established: Proxying '{api_prefix}' to port {backend_port}[/bold magenta]"
    )
    return f"Success: Synaptic routing configured. Vite will now proxy {api_prefix} to localhost:{backend_port}."
