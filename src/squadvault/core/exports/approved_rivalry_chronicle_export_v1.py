"""Export approved rivalry chronicle artifacts from the database."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Set

from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1
from squadvault.core.storage.db_utils import table_columns as _table_columns
from squadvault.core.storage.session import DatabaseSession
from squadvault.errors import SchemaError, RecapNotFoundError


def _pick_first(existing: Set[str], candidates: List[str]) -> str | None:
    """Return first column name from candidates that exists in cols, or None."""
    for c in candidates:
        if c in existing:
            return c
    return None


@dataclass(frozen=True)
class ApprovedRivalryChronicleArtifactV1:
    league_id: int
    season: int
    anchor_week_index: int
    artifact_type: str
    version: int
    selection_fingerprint: str
    provenance: Dict[str, Any]
    rendered_text: str


def fetch_latest_approved_rivalry_chronicle_v1(db_path: str) -> ApprovedRivalryChronicleArtifactV1:
    """
    Projection-only fetch of the latest APPROVED Rivalry Chronicle v1 artifact.

    - Reads recap_artifacts only
    - Hard-fails if none exists
    - No inference; provenance is stored columns only
    """
    debug = os.environ.get("SV_DEBUG") == "1"

    with DatabaseSession(db_path) as con:
        cols = _table_columns(con, "recap_artifacts")

        # Required columns for this exporter.
        required = [
            "id",
            "league_id",
            "season",
            "week_index",
            "artifact_type",
            "version",
            "state",
            "selection_fingerprint",
            "rendered_text",
        ]
        missing_required = [c for c in required if c not in cols]
        if missing_required:
            raise SchemaError(f"recap_artifacts missing required columns: {missing_required}")

        # Optional provenance fields (use whichever naming exists; store “as-is”).
        created_col = _pick_first(cols, ["created_at_utc", "created_at"])
        approved_at_col = _pick_first(cols, ["approved_at_utc", "approved_at"])
        approved_by_col = _pick_first(cols, ["approved_by"])
        supersedes_col = _pick_first(cols, ["supersedes_version"])
        withheld_col = _pick_first(cols, ["withheld_reason"])

        select_cols = list(required)
        for c in [created_col, approved_at_col, approved_by_col, supersedes_col, withheld_col]:
            if c and c not in select_cols:
                select_cols.append(c)

        # Deterministic ordering: prefer approved timestamp if present, else fall back to id.
        order_terms: List[str] = []
        if approved_at_col:
            order_terms.append(f"{approved_at_col} DESC")
        order_terms.append("id DESC")
        order_by = ", ".join(order_terms)

        sql = (
            "SELECT\n  "
            + ",\n  ".join(select_cols)
            + "\nFROM recap_artifacts\n"
            + "WHERE artifact_type = ?\n  AND state = 'APPROVED'\n"
            + f"ORDER BY {order_by}\n"
            + "LIMIT 1\n"
        )

        row = con.execute(sql, (str(ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1),)).fetchone()

        if row is None:
            raise RecapNotFoundError("No APPROVED RIVALRY_CHRONICLE_V1 artifact found.")

        provenance: Dict[str, Any] = {
            "id": int(row["id"]),
            "state": str(row["state"]),
        }
        if created_col and row[created_col] is not None:
            provenance[created_col] = row[created_col]
        if approved_at_col and row[approved_at_col] is not None:
            provenance[approved_at_col] = row[approved_at_col]
        if approved_by_col and row[approved_by_col] is not None:
            provenance[approved_by_col] = row[approved_by_col]
        if supersedes_col and row[supersedes_col] is not None:
            provenance[supersedes_col] = row[supersedes_col]
        if withheld_col and row[withheld_col] is not None:
            provenance[withheld_col] = row[withheld_col]

        if debug:
            print(
                f"SV_DEBUG=1: fetched APPROVED {ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1} "
                f"league={row['league_id']} season={row['season']} week_index={row['week_index']} v{row['version']}",
                file=sys.stderr,
            )
            print(f"SV_DEBUG=1: provenance_keys={sorted(provenance.keys())}", file=sys.stderr)

        rendered_text = row["rendered_text"] or ""

        return ApprovedRivalryChronicleArtifactV1(
            league_id=int(row["league_id"]),
            season=int(row["season"]),
            anchor_week_index=int(row["week_index"]),
            artifact_type=str(row["artifact_type"]),
            version=int(row["version"]),
            selection_fingerprint=str(row["selection_fingerprint"]),
            provenance=provenance,
            rendered_text=str(rendered_text),
        )
