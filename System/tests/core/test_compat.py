from typing import List, Optional
from System.core.compat import get_safe_annotations


def _dummy_tool_function(param_a: int, param_b: Optional[str]) -> List[int]:
    """A dummy signature to verify type hint extraction."""
    return [param_a]


def test_get_safe_annotations_resolves_correctly() -> None:
    """Verifies the 3.14 polyfill accurately resolves complex types."""
    annotations = get_safe_annotations(_dummy_tool_function)

    # 1. Verify standard types
    assert annotations.get("param_a") is int

    # 2. Verify wrapped/complex types (Optional/Union)
    assert "str" in str(annotations.get("param_b"))

    # 3. Verify return types
    assert "list" in str(annotations.get("return")).lower()
