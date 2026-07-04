"""Manual import orchestration: C3 approval gate + conflict surfacing (Unit A8).

The explicit, auditable founder act that admits commissioner-attested auction facts:
  - C3 approval (no silent ingestion): an import proceeds only against a recorded approval
    (who / when / which artifact-by-hash). require_approval() refuses otherwise.
  - Conflict surfacing (never resolution): where a manual fact and an existing canonical (MFL)
    fact disagree, the canonical fact WINS and is left untouched; the discrepancy is reported.
    The adapter never modifies, supersedes, or shadows a canonical fact.
  - Append-only write: envelopes go to memory_events via SQLiteStore.append_events (idempotent
    by (external_source, external_id)); re-import is a no-op.

Pure of the derivation logic (that is manual_auction.py); this module is the DB-touching seam,
used by the CLI entry tool. It writes to whatever store it is handed - the CLI hands it a SCRATCH
store; prod entry remains a separate founder act.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.manual_auction import is_manual_source


def _now_iso_z() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ApprovalRequiredError(RuntimeError):
    """An import was attempted with no matching C3 approval - refused (no silent ingestion)."""


@dataclass(frozen=True)
class ImportConflict:
    """A manual fact that disagrees with an existing canonical fact. Surfaced, not resolved."""

    league_id: str
    season: int
    franchise_id: str
    player_id: str
    manual_bid: float
    canonical_bid: float
    canonical_external_source: str


def record_approval(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    external_source: str,
    source_artifact_sha256: str,
    actor: str,
    notes: str | None = None,
) -> None:
    """Record the C3 attributed approval (idempotent by the natural key)."""
    with store.connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO manual_import_approvals
              (league_id, season, external_source, source_artifact_sha256, actor, approved_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (league_id, int(season), external_source, source_artifact_sha256, actor, _now_iso_z(), notes),
        )
        conn.commit()


def has_approval(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    external_source: str,
    source_artifact_sha256: str,
) -> bool:
    """True iff a C3 approval row authorizes this (league, season, provenance, artifact-hash)."""
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM manual_import_approvals
            WHERE league_id = ? AND season = ? AND external_source = ? AND source_artifact_sha256 = ?
            LIMIT 1
            """,
            (league_id, int(season), external_source, source_artifact_sha256),
        ).fetchone()
    return row is not None


def require_approval(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    external_source: str,
    source_artifact_sha256: str,
) -> None:
    """Raise ApprovalRequiredError unless a matching C3 approval exists."""
    if not has_approval(
        store,
        league_id=league_id,
        season=season,
        external_source=external_source,
        source_artifact_sha256=source_artifact_sha256,
    ):
        raise ApprovalRequiredError(
            f"no C3 approval for {external_source} / {league_id} / {season} / "
            f"{source_artifact_sha256[:12]}...: attestation is an explicit founder act per import"
        )


def find_canonical_conflicts(
    store: SQLiteStore, manual_events: list[dict[str, Any]]
) -> list[ImportConflict]:
    """Report where a manual fact disagrees with an existing non-manual DRAFT_PICK.

    A conflict is a same (league, season, franchise, player) canonical (non-MANUAL) DRAFT_PICK whose
    bid_amount differs from the manual fact's. Canonical WINS: nothing is mutated; the discrepancy
    is returned for surfacing. (The manual row still lands in its distinct identity space; the two
    coexist and the conflict is visible, per contract section 4.)
    """
    conflicts: list[ImportConflict] = []
    with store.connect() as conn:
        for ev in manual_events:
            payload = ev.get("payload") or {}
            fr = str(payload.get("franchise_id") or "")
            pl = str(payload.get("player_id") or "")
            manual_bid = float(payload.get("bid_amount") or 0.0)
            # Compare against the CANONICAL (gold) fact, not the raw ledger: downstream reads go
            # through v_canonical_best_events (memory_events is the internal ledger). This also
            # means we conflict only against a canonicalized fact, which is the one that "wins".
            rows = conn.execute(
                """
                SELECT external_source, payload_json
                FROM v_canonical_best_events
                WHERE league_id = ? AND season = ? AND event_type = 'DRAFT_PICK'
                  AND json_extract(payload_json, '$.franchise_id') = ?
                  AND json_extract(payload_json, '$.player_id') = ?
                """,
                (ev["league_id"], int(ev["season"]), fr, pl),
            ).fetchall()
            for r in rows:
                src = r["external_source"]
                if is_manual_source(src):
                    continue  # compare only against canonical (non-manual) facts
                import json as _json

                canonical_bid = float((_json.loads(r["payload_json"]) or {}).get("bid_amount") or 0.0)
                if canonical_bid != manual_bid:
                    conflicts.append(
                        ImportConflict(
                            league_id=str(ev["league_id"]),
                            season=int(ev["season"]),
                            franchise_id=fr,
                            player_id=pl,
                            manual_bid=manual_bid,
                            canonical_bid=canonical_bid,
                            canonical_external_source=str(src),
                        )
                    )
    return conflicts


@dataclass(frozen=True)
class ImportResult:
    inserted: int
    skipped: int
    conflicts: list[ImportConflict]


def import_manual_events(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    external_source: str,
    source_artifact_sha256: str,
    envelopes: list[dict[str, Any]],
) -> ImportResult:
    """Admit manual envelopes: require C3 approval, surface conflicts, append-only write.

    Refuses (ApprovalRequiredError) if no C3 approval authorizes this import. Conflicts are
    surfaced in the result but do NOT block the manual row (it lands in its distinct identity
    space); canonical facts are never mutated.
    """
    require_approval(
        store,
        league_id=league_id,
        season=season,
        external_source=external_source,
        source_artifact_sha256=source_artifact_sha256,
    )
    conflicts = find_canonical_conflicts(store, envelopes)
    inserted, skipped = store.append_events(envelopes)
    return ImportResult(inserted=inserted, skipped=skipped, conflicts=conflicts)
