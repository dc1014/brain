import os
from pathlib import Path
from typing import Union

#  The root directory itself must be fully resolved to its true physical address
ROOT_DIR = (
    Path(os.path.realpath(str(Path(__file__).parent.parent.parent)))
    .resolve()
    .absolute()
)


def normalize_path(path_input: Union[str, Path]) -> Path:
    """
    Eradicates cross-platform string inconsistencies (e.g., Windows casing, relative traversal)
    by enforcing a strict, absolute, resolved pathlib.Path object.

    SYMLINK ARMOR: Path.resolve() permanently strips away all symlinks,
    Windows junctions, and relative hooks before resolving the absolute path.
    """
    # .expanduser() handles "~", .resolve() handles symlinks and absolute conversions natively
    return Path(path_input).expanduser().resolve()
