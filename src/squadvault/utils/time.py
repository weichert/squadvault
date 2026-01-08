from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def unix_seconds_to_iso_z(unix_seconds: int | None) -> Optional[str]:
    if unix_seconds is None:
        return None
    try:
        dt = datetime.fromtimestamp(int(unix_seconds), tz=timezone.utc)
        # Notion accepts ISO 8601; use Zulu.
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None
