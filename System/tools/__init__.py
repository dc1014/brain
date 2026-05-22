# --- System/tools/__init__.py ---

from typing import Any
from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from rich.panel import Panel
from rich.text import Text

# ⚡ CORE DEPENDENCIES
from .sandbox import is_safe_path, execute_in_sandbox, ALLOWED_DIRECTORIES

# 🐳 EXECUTION LAYERS
from .execution import (
    execute_command,
    execute_command_async,
    analyze_safe_syntax,
    deploy_project,
    deploy_project_async,
    manage_background_process,
    is_port_in_use,
)

# 📁 FILE SYSTEM LAYERS
from .file_system import (
    read_safe_file,
    write_safe_file,
    append_safe_file,
    delete_safe_file,
    copy_safe_file,
    rename_safe_file,
    list_safe_directory,
    write_multiple_files,
)

# 👁️ SENSORY COUPLING
from .sensory import (
    sense_environment,
    analyze_image,
    generate_image,
    capture_screenshot,
    speak,
    analyze_audio,
    taste_safe_file,
    analyze_video,
    perceive_webcam,
    memorize_user_appearance,
    record_user_video,
)

# 🧠 COGNITIVE COUPLING
from .cognitive import (
    read_file_signatures,
    search_safe_directory,
    semantic_search,
    search_hippocampus,
    create_engram_tool,
    list_engrams_tool,
    execute_engram_tool,
    map_spatial_dependencies,
    configure_synaptic_routing_tool,
    map_system_topology_tool,
    transmit_telepathy,
)

# ⚡ DYNAMIC/OPTIONAL REGISTRATIONS: Signatures identically mirror the original imports
try:
    from .forge import bootstrap_project, operate_forge
except Exception:

    def bootstrap_project(
        project_name: str,
        template_url: str = "https://github.com/mrdanielcasper/forge.git",
    ) -> ExecutionResult:
        return ExecutionResult(success=False, output="", block_reason="Fallback")

    def operate_forge(project_name: str, instruction: str) -> ExecutionResult:
        return ExecutionResult(success=False, output="", block_reason="Fallback")


try:
    from .motor import act
except Exception:

    def act(action: str, target: str = "") -> Any:
        return None


try:
    from .diagnostic import get_system_vitals
except Exception:

    def get_system_vitals() -> Panel:
        return Panel(Text("Fallback Ledger Data"))


try:
    from .topology import map_system_topology
except Exception:

    def map_system_topology(format_type: str) -> str:
        return ""


# ⚡ LINT STUBS
def look(*args: Any, **kwargs: Any) -> Any:
    return None


def listen(*args: Any, **kwargs: Any) -> Any:
    return None


def think(*args: Any, **kwargs: Any) -> Any:
    return None


def remember(*args: Any, **kwargs: Any) -> Any:
    return None


def recall(*args: Any, **kwargs: Any) -> Any:
    return None


def learn(*args: Any, **kwargs: Any) -> Any:
    return None


# ⚡ INTERNAL ATTRIBUTE BACK-MAPPING
execute_engram = execute_engram_tool


# ==============================================================================
# 🛡️ THE EXPLICIT MYPY/RUFF EXPORT BARRIER
# Completely prevents circular analysis failures by hardcoding the public API.
# ==============================================================================
__all__ = [
    "ROOT_DIR",
    "normalize_path",
    "ExecutionResult",
    "Panel",
    "Text",
    "is_safe_path",
    "execute_in_sandbox",
    "ALLOWED_DIRECTORIES",
    "execute_command",
    "execute_command_async",
    "analyze_safe_syntax",
    "deploy_project",
    "deploy_project_async",
    "manage_background_process",
    "is_port_in_use",
    "read_safe_file",
    "write_safe_file",
    "append_safe_file",
    "delete_safe_file",
    "copy_safe_file",
    "rename_safe_file",
    "list_safe_directory",
    "write_multiple_files",
    "sense_environment",
    "analyze_image",
    "generate_image",
    "capture_screenshot",
    "speak",
    "analyze_audio",
    "taste_safe_file",
    "analyze_video",
    "perceive_webcam",
    "memorize_user_appearance",
    "record_user_video",
    "read_file_signatures",
    "search_safe_directory",
    "semantic_search",
    "search_hippocampus",
    "create_engram_tool",
    "list_engrams_tool",
    "execute_engram_tool",
    "execute_engram",
    "map_spatial_dependencies",
    "configure_synaptic_routing_tool",
    "map_system_topology_tool",
    "transmit_telepathy",
    "bootstrap_project",
    "operate_forge",
    "act",
    "get_system_vitals",
    "map_system_topology",
    "look",
    "listen",
    "think",
    "remember",
    "recall",
    "learn",
]
