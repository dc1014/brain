import subprocess  # Re-expose for tests that mock System.tools.subprocess
from System.core.paths import ROOT_DIR  # Re-expose for external organs
from .sandbox import is_safe_path, ALLOWED_DIRECTORIES, READ_ONLY_DIRECTORIES

# Re-export all motor functions
from .file_system import (
    write_safe_file,
    read_safe_file,
    list_safe_directory,
    rename_safe_file,
    append_safe_file,
    copy_safe_file,
    delete_safe_file,
    write_multiple_files,
)
from .execution import (
    execute_command,
    analyze_safe_syntax,
    manage_background_process,
)
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
from .cognitive import (
    read_file_signatures,
    search_safe_directory,
    semantic_search,
    search_hippocampus,
    create_engram_tool,
    list_engrams_tool,
    execute_engram_tool,
    map_spatial_dependencies,
)
from .forge import (
    operate_forge,
    bootstrap_project,
)

__all__ = [
    "sandbox",
    "subprocess",
    "ROOT_DIR",
    "is_safe_path",
    "ALLOWED_DIRECTORIES",
    "READ_ONLY_DIRECTORIES",
    "write_safe_file",
    "read_safe_file",
    "list_safe_directory",
    "rename_safe_file",
    "append_safe_file",
    "copy_safe_file",
    "delete_safe_file",
    "execute_command",
    "analyze_safe_syntax",
    "manage_background_process",
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
    "map_spatial_dependencies",
    "operate_forge",
    "bootstrap_project",
    "write_multiple_files",
]
