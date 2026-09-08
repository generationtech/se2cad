"""Late-bound SolidWorks COM attribute access.

SolidWorks 2026 + pywin32 returns CDispatch. Properties such as
FirstFeature and RevisionNumber already resolve on attribute access.
Calling those CDispatch values invokes a default member and fails with
DISP_E_MEMBERNOTFOUND. Methods still need a call.
"""

from __future__ import annotations

from typing import Any

_DISP_E_MEMBERNOTFOUND = -2147352573


def com_get(obj: Any, name: str, *args: Any) -> Any:
    """Return a COM property or the result of a COM method."""
    attr = getattr(obj, name)
    if args:
        return attr(*args)
    if not callable(attr):
        return attr
    try:
        return attr()
    except Exception as exc:
        code = getattr(exc, "args", (None,))[0]
        if code == _DISP_E_MEMBERNOTFOUND and getattr(attr, "_oleobj_", None) is not None:
            return attr
        raise
