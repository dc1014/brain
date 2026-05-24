import sys
from typing import Any, Dict


def get_safe_annotations(obj: Any) -> Dict[str, Any]:
    """
    🛡️ ZERO-DEBT REFLECTION: Safely pulls runtime type maps across Python versions.
    Resolves PEP 649/749 deferred evaluation changes in Python 3.14 natively,
    while maintaining flawless backward compatibility with 3.12 and 3.13.
    """
    if sys.version_info >= (3, 14):
        # Python 3.14+ uses lazy evaluation descriptors via annotationlib
        import annotationlib  # type: ignore[import-not-found, import-untyped]

        # Format.VALUE forces the immediate resolution of the deferred type objects
        return annotationlib.get_annotations(
            obj,
            format=annotationlib.Format.VALUE,  # type: ignore[attr-defined]
        )
    else:
        # Python 3.12 and 3.13 standard behavior
        import typing

        return typing.get_type_hints(obj)
