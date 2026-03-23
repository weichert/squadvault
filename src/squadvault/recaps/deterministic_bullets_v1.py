"""DEPRECATED — canonical location is squadvault.core.recaps.render.deterministic_bullets_v1.

This shim will be removed in a future version. Update imports to:
    from squadvault.core.recaps.render.deterministic_bullets_v1 import ...
"""
import warnings as _w
_w.warn(
    "squadvault.recaps.deterministic_bullets_v1 is deprecated. "
    "Use squadvault.core.recaps.render.deterministic_bullets_v1.",
    DeprecationWarning, stacklevel=2,
)
from squadvault.core.recaps.render.deterministic_bullets_v1 import (  # noqa: F401
    CanonicalEventRow,
    MAX_BULLETS,
    QUIET_WEEK_MIN_EVENTS,
    render_deterministic_bullets_v1,
    _ascii_punct,
    _money,
    _safe,
)
