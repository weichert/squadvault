"""Re-export shim — canonical location is squadvault.recaps.weekly_recap_lifecycle

This file exists for backward compatibility only. All logic lives in
squadvault.recaps.weekly_recap_lifecycle.
"""
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
