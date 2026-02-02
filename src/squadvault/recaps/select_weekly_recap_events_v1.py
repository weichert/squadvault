"""
Compatibility shim.

Consumers should import weekly selection via this module so internal refactors
don't break CLIs/consumers.
"""

from __future__ import annotations

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1

__all__ = ["select_weekly_recap_events_v1"]
