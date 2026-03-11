"""Re-export shim — canonical location is squadvault.core.recaps.render.deterministic_bullets_v1"""
from squadvault.core.recaps.render.deterministic_bullets_v1 import (  # noqa: F401
    CanonicalEventRow,
    MAX_BULLETS,
    QUIET_WEEK_MIN_EVENTS,
    render_deterministic_bullets_v1,
    _ascii_punct,
    _money,
    _safe,
)
