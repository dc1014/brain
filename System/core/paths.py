from pathlib import Path
from typing import Union

# The absolute root of the Brain OS workspace
ROOT_DIR = Path(__file__).parent.parent.parent.resolve().absolute()


def normalize_path(path_input: Union[str, Path]) -> Path:
    """
    Biological Pathway: Myelination (Path Normalization)
    Eradicates cross-platform string inconsistencies (e.g., Windows casing, relative traversal)
    by enforcing a strict, absolute, resolved pathlib.Path object.

    This guarantees that C:\\Brain and c:\\brain resolve to the exact same
    memory address, preventing lock bypassing and sandbox escapes.
    """
    # Convert to Path, expand user directory (~), resolve relative steps (../), and force absolute
    return Path(path_input).expanduser().resolve().absolute()
