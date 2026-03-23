"""DEPRECATED — canonical location is squadvault.recaps.weekly_recap_lifecycle.

This shim will be removed in a future version. Update imports to:
    from squadvault.recaps.weekly_recap_lifecycle import ...
"""
import warnings as _w
_w.warn(
    "squadvault.core.recaps.weekly_recap_lifecycle is deprecated. "
    "Use squadvault.recaps.weekly_recap_lifecycle.",
    DeprecationWarning, stacklevel=2,
)
from squadvault.recaps.weekly_recap_lifecycle import (  # noqa: F401
    ARTIFACT_TYPE_WEEKLY_RECAP,
    ApproveResult,
    GenerateDraftResult,
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
    get_recap_run_state,
    latest_approved_version,
    sync_recap_run_state_from_artifacts,
)
