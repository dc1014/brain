# ruff: noqa: E402
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# CORE DEPENDENCIES
from .sandbox import (
    is_safe_path as is_safe_path,
    execute_in_sandbox as execute_in_sandbox,
    ALLOWED_DIRECTORIES as ALLOWED_DIRECTORIES,
)

# EXECUTION LAYERS
from .execution import (
    execute_command as execute_command,
    execute_command_async as execute_command_async,
    analyze_safe_syntax as analyze_safe_syntax,
    deploy_project as deploy_project,
    deploy_project_async as deploy_project_async,
    manage_background_process as manage_background_process,
    is_port_in_use as is_port_in_use,
)

# FILE SYSTEM LAYERS
from .file_system import (
    read_safe_file as read_safe_file,
    write_safe_file as write_safe_file,
    append_safe_file as append_safe_file,
    delete_safe_file as delete_safe_file,
    copy_safe_file as copy_safe_file,
    rename_safe_file as rename_safe_file,
    list_safe_directory as list_safe_directory,
    write_multiple_files as write_multiple_files,
)

# SENSORY COUPLING
from .sensory import (
    sense_environment as sense_environment,
    analyze_image as analyze_image,
    generate_image as generate_image,
    capture_screenshot as capture_screenshot,
    speak as speak,
    analyze_audio as analyze_audio,
    taste_safe_file as taste_safe_file,
    analyze_video as analyze_video,
    perceive_webcam as perceive_webcam,
    memorize_user_appearance as memorize_user_appearance,
    record_user_video as record_user_video,
)

# COGNITIVE COUPLING
from .topology import map_system_topology as map_system_topology

from .cognitive import (
    read_file_signatures as read_file_signatures,
    search_safe_directory as search_safe_directory,
    semantic_search as semantic_search,
    search_hippocampus as search_hippocampus,
    create_engram_tool as create_engram_tool,
    list_engrams_tool as list_engrams_tool,
    execute_engram_tool as execute_engram_tool,
    map_spatial_dependencies as map_spatial_dependencies,
    configure_synaptic_routing_tool as configure_synaptic_routing_tool,
    map_system_topology_tool as map_system_topology_tool,
    transmit_telepathy as transmit_telepathy,
)

execute_engram = execute_engram_tool
list_engrams = list_engrams_tool

# PROJECT FORGE LAYER
from .forge import bootstrap_project as bootstrap_project
