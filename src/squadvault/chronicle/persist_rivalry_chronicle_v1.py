"""Persist generated rivalry chronicle artifacts to the database."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional, Tuple

from squadvault.errors import SchemaError
from squadvault.core.storage.db_utils import table_columns as _table_columns
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1
from squadvault.chronicle.generate_rivalry_chronicle_v1 import (
    RivalryChronicleGeneratedV1,
    generate_rivalry_chronicle_v1,
)
from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy
from squadvault.core.storage.session import DatabaseSession


def _insert_recap_artifact_row_schema_resilient(
    conn: sqlite3.Connection,
    *,
    league_id: int,
    season: int,
    week_index: int,
    artifact_type: str,
    version: int,
    state: str,
    selection_fingerprint: str,
    rendered_text: str,
    created_at_utc: str,
) -> None:
    """Insert a recap_artifact row with dynamic column detection for schema resilience."""
    cols = _table_columns(conn, "recap_artifacts")

    # Required core columns (must exist or we hard fail)
    required = ["league_id", "season", "week_index", "artifact_type", "version", "state"]
    missing_required = [c for c in required if c not in cols]
    if missing_required:
        raise SchemaError(f"recap_artifacts missing required columns: {missing_required}")

    # Build insert columns dynamically
    insert_cols = ["league_id", "season", "week_index", "artifact_type", "version", "state"]
    insert_vals = [int(league_id), int(season), int(week_index), str(artifact_type), int(version), str(state)]

    if "selection_fingerprint" in cols:
        insert_cols.append("selection_fingerprint")
        insert_vals.append(str(selection_fingerprint))

    if "rendered_text" in cols:
        insert_cols.append("rendered_text")
        insert_vals.append(str(rendered_text))

    # Prefer created_at_utc / approved_at_utc if present; else skip quietly.
    if "created_at_utc" in cols:
        insert_cols.append("created_at_utc")
        insert_vals.append(str(created_at_utc))

    if "approved_at_utc" in cols:
        insert_cols.append("approved_at_utc")
        insert_vals.append(str(created_at_utc))

    # Some schemas may use created_at / approved_at (non-UTC). Only set if present.
    if "created_at" in cols and "created_at_utc" not in cols:
        insert_cols.append("created_at")
        insert_vals.append(str(created_at_utc))

    if "approved_at" in cols and "approved_at_utc" not in cols:
        insert_cols.append("approved_at")
        insert_vals.append(str(created_at_utc))

    ph = ",".join(["?"] * len(insert_cols))
    col_sql = ", ".join(insert_cols)

    conn.execute(
        f"INSERT INTO recap_artifacts ({col_sql}) VALUES ({ph})",
        insert_vals,
    )


@dataclass(frozen=True)
class PersistedChronicleV1:
    league_id: int
    season: int
    anchor_week_index: int
    artifact_type: str
    version: int
    created_new: bool


def _latest_approved_chronicle_row(
    conn: sqlite3.Connection, league_id: int, season: int, anchor_week_index: int
) -> Optional[sqlite3.Row]:
    """Return the latest approved rivalry chronicle artifact row, or None."""
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT version, selection_fingerprint
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = ?
          AND state = 'APPROVED'
        ORDER BY version DESC
        LIMIT 1
        """,
        (int(league_id), int(season), int(anchor_week_index), ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1),
    ).fetchone()
    return row  # type: ignore[no-any-return]


def _next_version(conn: sqlite3.Connection, league_id: int, season: int, anchor_week_index: int) -> int:
    """Return next sequential version number for rivalry chronicle artifacts."""
    row = conn.execute(
        """
        SELECT MAX(version)
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = ?
        """,
        (int(league_id), int(season), int(anchor_week_index), ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1),
    ).fetchone()
    max_v = row[0] if row else None
    return int(max_v or 0) + 1


def persist_rivalry_chronicle_v1(
    *,
    db_path: str,
    league_id: int,
    season: int,
    week_indices: Tuple[int, ...] | None,
    week_range: Tuple[int, int] | None,
    missing_weeks_policy: MissingWeeksPolicy,
    created_at_utc: str,
    team_a_id: str | None = None,
    team_b_id: str | None = None,
) -> PersistedChronicleV1:
    """Persist a generated rivalry chronicle as a versioned DRAFT artifact.

    Same governance model as Weekly Recap: generate produces DRAFT,
    explicit human approval transitions to APPROVED.
    """
    gen: RivalryChronicleGeneratedV1 = generate_rivalry_chronicle_v1(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week_indices=week_indices,
        week_range=week_range,
        missing_weeks_policy=missing_weeks_policy,
        created_at_utc=created_at_utc,
        team_a_id=team_a_id,
        team_b_id=team_b_id,
    )

    with DatabaseSession(db_path) as conn:
        conn.row_factory = sqlite3.Row

        # Idempotency: check if any artifact (DRAFT or APPROVED) already
        # has the same fingerprint for this anchor week
        existing = conn.execute(
            """
            SELECT version, state, selection_fingerprint
            FROM recap_artifacts
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = ?
              AND selection_fingerprint = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (int(league_id), int(season), int(gen.anchor_week_index),
             ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1, gen.fingerprint),
        ).fetchone()

        if existing is not None:
            return PersistedChronicleV1(
                league_id=int(league_id),
                season=int(season),
                anchor_week_index=int(gen.anchor_week_index),
                artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
                version=int(existing["version"]),
                created_new=False,
            )

        new_v = _next_version(conn, league_id, season, gen.anchor_week_index)

        _insert_recap_artifact_row_schema_resilient(
            conn,
            league_id=int(league_id),
            season=int(season),
            week_index=int(gen.anchor_week_index),
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=int(new_v),
            state="DRAFT",
            selection_fingerprint=str(gen.fingerprint),
            rendered_text=str(gen.text),
            created_at_utc=str(created_at_utc),
        )
        conn.commit()

        return PersistedChronicleV1(
            league_id=int(league_id),
            season=int(season),
            anchor_week_index=int(gen.anchor_week_index),
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            version=int(new_v),
            created_new=True,
        )
