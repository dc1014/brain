import os
from pathlib import Path
from typing import Union

# ⚡ SYMLINK ARMOR: The root directory itself must be fully resolved to its true physical address
ROOT_DIR = (
    Path(os.path.realpath(str(Path(__file__).parent.parent.parent)))
    .resolve()
    .absolute()
)


def normalize_path(path_input: Union[str, Path]) -> Path:
    """
    Biological Pathway: Myelination (Path Normalization)
    Eradicates cross-platform string inconsistencies (e.g., Windows casing, relative traversal)
    by enforcing a strict, absolute, resolved pathlib.Path object.

    This guarantees that C:\\Brain and c:\\brain resolve to the exact same
    memory address, preventing lock bypassing and sandbox escapes.
    """
    raw_path = Path(path_input).expanduser()

    # ⚡ SYMLINK ARMOR: os.path.realpath permanently strips away all symlinks,
    # Windows junctions, and relative hooks before resolving the absolute path.
    # It guarantees we are evaluating the TRUE physical destination of the payload.
    true_physical_path = os.path.realpath(str(raw_path))

    return Path(true_physical_path).resolve().absolute()
