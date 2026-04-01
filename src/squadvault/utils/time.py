"""Time conversion utilities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
def unix_seconds_to_iso_z(unix_seconds: int | None) -> str | None:
    """Convert Unix timestamp to ISO-8601 UTC string."""
    if unix_seconds is None:
        return None
    try:
        dt = datetime.fromtimestamp(int(unix_seconds), tz=timezone.utc)
        # Notion accepts ISO 8601; use Zulu.
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as exc:
        logger.debug("%s", exc)
        return None


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
