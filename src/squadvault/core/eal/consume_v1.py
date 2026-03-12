#!/usr/bin/env python3
"""Load EAL directives from recap_runs for render-time consumption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import sqlite3
from squadvault.core.storage.session import DatabaseSession


# IMPORTANT:
# - Read-only consumer boundary for EAL v1.
# - Takes a recap_run_id.
# - Returns directives ONLY.
# - Safe if EAL persistence table does not exist.


@dataclass(frozen=True)
class EALDirectivesV1:
    tone_guard: Optional[str] = None
    privacy_guard: Optional[str] = None
    rivalry_heat_cap: Optional[int] = None
    allow_humiliation: Optional[bool] = None


def load_eal_directives_v1(
    db_path: str,
    recap_run_id: str,
) -> Optional[EALDirectivesV1]:
    """
    Read persisted EAL directives for a given recap_run_id.

    Semantics:
      - If table does not exist → return None
      - If no row exists → return None
      - Otherwise → return EALDirectivesV1
    """
    with DatabaseSession(db_path) as con:
        cur = con.cursor()
        try:
            cur.execute(
                """
                SELECT directives_json
                FROM eal_directives_v1
                WHERE recap_run_id = ?
                ORDER BY created_at_utc DESC
                LIMIT 1
                """,
                (recap_run_id,),
            )
        except sqlite3.OperationalError:
            # Table does not exist → neutral
            return None

        row = cur.fetchone()
        if not row or row[0] is None:
            return None

        payload: Dict[str, Any] = json.loads(row[0])

        return EALDirectivesV1(
            tone_guard=payload.get("tone_guard"),
            privacy_guard=payload.get("privacy_guard"),
            rivalry_heat_cap=payload.get("rivalry_heat_cap"),
            allow_humiliation=payload.get("allow_humiliation"),
        )
