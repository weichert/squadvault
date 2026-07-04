"""Manual Source Adapter: commissioner-attested auction facts (Unit A8).

Governed entry path for human-attested auction acquisition amounts, per the RATIFIED
Manual Source Adapter Contract v1.0 (docs/contracts/manual_source_adapter_contract_v1.md).

Constitutional shape (contract-governed; NOT the brief's superseded "attested-fact table"):
- No schema change to the event ledger, no new event type. Manual auction facts are ordinary
  DRAFT_PICK envelopes written to the existing append-only memory_events table (envelope model).
- Provenance rides `external_source = "MANUAL:<tag>"` (C1): load-bearing, never strippable. The
  dedup tuple (league_id, season, external_source, external_id) keeps manual and live (MFL) facts
  in DISTINCT identity spaces, so a manual row can never modify, supersede, or shadow a canonical
  MFL row.
- Determinism (C1/§3): external_id is a function of ARTIFACT-NATIVE fields ONLY
  (league_id, season, "DRAFT_PICK", franchise_id, player_id, bid_amount) - never a timestamp or
  ingest index (the bulk artifact carries none). Re-import is a byte-identical no-op via
  INSERT OR IGNORE.
- Retention (C2/D3): the origin workbook is retained ONCE, content-addressed; each row's payload
  carries source_artifact_sha256 + source_artifact_ref (re-inspectability, not re-fetchability).
- Partial truth (C4): only rows that reconcile to known identities AND pass the LOAD_ROSTERS
  integrity anchor import; everything else is HELD ABSENT and reported - never gap-filled.

Approval (C3) and the CLI founder-act live alongside this module; this file is pure derivation
(facts only, no DB writes, no I/O beyond hashing a retained artifact path).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# The manual auction win marker. Provenance lives in external_source (C1); this mfl_type is the
# artifact-native pick type, distinct from MFL's live "AUCTION_WON" so downstream selection that
# is (correctly) marker-aware includes it without a source branch. See select_auction_winners.
MANUAL_AUCTION_WON = "MANUAL_AUCTION_WON"

# Contaminant pick types that a winner selection MUST exclude (never a whitelist of win types).
# Intermediate auction bids are not acquisitions; whitelisting "AUCTION_WON" would silently drop
# manual rows (marker MANUAL_AUCTION_WON) and any future adapter's win string (contract section 2).
AUCTION_CONTAMINANT_TYPES: frozenset[str] = frozenset({"AUCTION_BID"})

_MANUAL_SOURCE_PREFIX = "MANUAL:"


class ManualProvenanceError(ValueError):
    """A manual envelope carried a malformed provenance tag (T4.3 / C1 non-strippability)."""


def manual_external_source(tag: str) -> str:
    """Build and validate a MANUAL-class external_source. Rejects an empty/blank tag (T4.3)."""
    src = f"{_MANUAL_SOURCE_PREFIX}{tag}"
    if not is_valid_manual_external_source(src):
        raise ManualProvenanceError(
            f"malformed manual provenance tag {tag!r}: external_source must be "
            f"'MANUAL:<non-empty-tag>' - unlabeled/mangled provenance refuses entry"
        )
    return src


def is_valid_manual_external_source(external_source: str | None) -> bool:
    """True iff external_source is exactly 'MANUAL:<non-empty, non-blank tag>' (C1 form)."""
    if not isinstance(external_source, str):
        return False
    if not external_source.startswith(_MANUAL_SOURCE_PREFIX):
        return False
    tag = external_source[len(_MANUAL_SOURCE_PREFIX):]
    return tag.strip() != "" and tag == tag.strip()


def is_manual_source(external_source: str | None) -> bool:
    """True iff a row's provenance is the manual (human-attested) class."""
    return isinstance(external_source, str) and external_source.startswith(_MANUAL_SOURCE_PREFIX)


def stable_manual_external_id(
    *, league_id: str, season: int, franchise_id: str, player_id: str, bid_amount: float
) -> str:
    """Deterministic external_id over ARTIFACT-NATIVE fields only (contract section 3).

    Never a function of timestamp/index/internal state, so re-importing the same artifact yields
    byte-identical envelopes and INSERT OR IGNORE makes re-import a no-op. bid_amount is rendered
    without trailing float noise so 67 and 67.0 hash identically.
    """
    bid_str = f"{float(bid_amount):.2f}"
    raw = "|".join([league_id, str(int(season)), "DRAFT_PICK", franchise_id, player_id, bid_str])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def sha256_file(path: str) -> str:
    """Content-address a retained source artifact (C2/D3). Streams; returns the full hex digest."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class AttestedAuctionRow:
    """One extracted, identity-reconciled auction acquisition from the retained artifact.

    franchise_id/player_id must already be reconciled to canonical ids; an unreconciled row is
    represented with an empty id and is HELD ABSENT (C4) by the deriver.
    """

    franchise_id: str
    player_id: str
    bid_amount: float


@dataclass(frozen=True)
class HeldAbsent:
    """A row that did not import, with the reason - reported, never silently dropped (C4)."""

    row: AttestedAuctionRow
    reason: str


def build_roster_seed_index(load_rosters_events: list[dict[str, Any]]) -> set[tuple[str, str]]:
    """Build the (franchise_id, player_id) membership set from TRANSACTION_LOAD_ROSTERS events.

    The LOAD_ROSTERS seed is MFL adapter-grade (platform-verified): it is "the half of each fact
    that IS platform-verified" (contract section 6.4). Each seed row carries the franchise and its
    players_added_ids array. Rows with no franchise or an empty roster (e.g. the commissioner-init
    row transaction "|") contribute nothing.
    """
    seed: set[tuple[str, str]] = set()
    for ev in load_rosters_events:
        payload = ev.get("payload") or {}
        franchise_id = str(payload.get("franchise_id") or "").strip()
        if not franchise_id:
            continue
        added = payload.get("players_added_ids")
        if isinstance(added, str):
            added = [p for p in added.replace(",", "|").split("|") if p.strip()]
        if not isinstance(added, (list, tuple)):
            continue
        for pid in added:
            pid_s = str(pid).strip()
            if pid_s:
                seed.add((franchise_id, pid_s))
    return seed


def derive_manual_auction_envelopes(
    *,
    league_id: str,
    season: int,
    tag: str,
    rows: list[AttestedAuctionRow],
    source_artifact_sha256: str,
    source_artifact_ref: str,
    roster_seed: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[HeldAbsent]]:
    """Derive canonical DRAFT_PICK envelopes for commissioner-attested auction wins.

    Returns (envelopes, held_absent). Facts only; no DB writes. Enforces, in order:
      - C1 tag form (T4.3): a malformed tag raises ManualProvenanceError - the import refuses
        entry rather than writing unlabeled provenance.
      - C4 identity reconciliation: a row missing a franchise_id or player_id is HELD ABSENT.
      - section 6.4 LOAD_ROSTERS integrity anchor: a (franchise, player) not on the season's
        adapter-grade roster seed is HELD ABSENT (blocked) - never force-matched.
    """
    external_source = manual_external_source(tag)  # raises on malformed tag (T4.3)

    envelopes: list[dict[str, Any]] = []
    held: list[HeldAbsent] = []
    for row in rows:
        fr = (row.franchise_id or "").strip()
        pl = (row.player_id or "").strip()
        if not fr or not pl:
            held.append(HeldAbsent(row, "unreconciled identity (missing franchise_id or player_id)"))
            continue
        if (fr, pl) not in roster_seed:
            held.append(
                HeldAbsent(row, f"LOAD_ROSTERS anchor: ({fr},{pl}) not on the {season} roster seed")
            )
            continue

        external_id = stable_manual_external_id(
            league_id=league_id, season=season, franchise_id=fr, player_id=pl, bid_amount=row.bid_amount
        )
        envelopes.append(
            {
                "event_type": "DRAFT_PICK",
                "occurred_at": None,  # bulk artifact carries no timestamp; NULL tolerated by schema
                "external_source": external_source,
                "external_id": external_id,
                "league_id": league_id,
                "season": int(season),
                "payload": {
                    "mfl_type": MANUAL_AUCTION_WON,
                    "franchise_id": fr,
                    "player_id": pl,
                    "bid_amount": float(row.bid_amount),
                    "source_artifact_sha256": source_artifact_sha256,
                    "source_artifact_ref": source_artifact_ref,
                },
            }
        )
    return envelopes, held


def select_auction_winners(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Marker-AWARE winning-pick selection (contract section 2; load-bearing).

    Selects acquisitions by EXCLUDING contaminant pick types and de-duping, NEVER by whitelisting a
    single live-source win string. A whitelist on 'AUCTION_WON' would silently drop manual rows
    (marker MANUAL_AUCTION_WON) and break for any future adapter's win type - the exact regression
    TA.1 guards. De-dup key is (external_source, external_id) so a MANUAL row and an MFL row for the
    same player remain distinct facts (distinct identity spaces), while a re-listed identical row
    collapses.
    """
    winners: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for ev in events:
        if ev.get("event_type") != "DRAFT_PICK":
            continue
        payload = ev.get("payload") or {}
        mfl_type = str(payload.get("mfl_type") or "")
        if mfl_type in AUCTION_CONTAMINANT_TYPES:
            continue
        key = (str(ev.get("external_source") or ""), str(ev.get("external_id") or ""))
        if key in seen:
            continue
        seen.add(key)
        winners.append(ev)
    return winners
