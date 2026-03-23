"""DEPRECATED — canonical location is squadvault.core.recaps.selection.weekly_selection_v1.

This shim will be removed in a future version. Update imports to:
    from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
"""

from __future__ import annotations

import warnings as _w
_w.warn(
    "squadvault.recaps.select_weekly_recap_events_v1 is deprecated. "
    "Use squadvault.core.recaps.selection.weekly_selection_v1.",
    DeprecationWarning, stacklevel=2,
)

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1

__all__ = ["select_weekly_recap_events_v1"]
