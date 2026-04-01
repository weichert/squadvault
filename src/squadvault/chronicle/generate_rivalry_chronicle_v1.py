"""Generate rivalry chronicle artifacts from canonical matchup events."""

# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT_CONTRACT_V1
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from squadvault.chronicle.approved_recap_refs_v1 import load_latest_approved_recap_refs_v1
from squadvault.chronicle.format_rivalry_chronicle_v1 import (
    UpstreamRecapQuoteV1,
    render_rivalry_chronicle_contract_v1,
    render_rivalry_chronicle_v1,
)
from squadvault.chronicle.input_contract_v1 import (
    ChronicleInputResolverV1,
    MissingWeeksPolicy,
    RivalryChronicleInputV1,
)
from squadvault.chronicle.matchup_facts_v1 import (
    facts_block_hash_v1,
    query_head_to_head_matchups_v1,
)
from squadvault.core.exports.approved_weekly_recap_export_v1 import fetch_latest_approved_weekly_recap
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_WEEKLY_RECAP
from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)

ARTIFACT_TYPE_RIVALRY_CHRONICLE = "RIVALRY_CHRONICLE"


def chronicle_fingerprint_v1(
    *,
    league_id: int,
    season: int,
    weeks_requested: Sequence[int],
    missing_weeks: Sequence[int],
    approved_recaps: Sequence[tuple[int, str, int, str]],
    team_a_id: str | None = None,
    team_b_id: str | None = None,
    matchup_facts_hash: str | None = None,
) -> str:
    """Compute deterministic fingerprint for a rivalry chronicle."""
    payload: dict = {
        "chronicle_version": 1,
        "league_id": int(league_id),
        "season": int(season),
        "weeks_requested": list(weeks_requested),
        "missing_weeks": list(missing_weeks),
        # Each tuple: (week_index, artifact_type, version, selection_fingerprint)
        "approved_recaps": list(approved_recaps),
    }
    # Include team pair in fingerprint when provided (deterministic sort)
    if team_a_id is not None and team_b_id is not None:
        sorted_pair = sorted([str(team_a_id), str(team_b_id)])
        payload["team_pair"] = sorted_pair
    if matchup_facts_hash is not None:
        payload["matchup_facts_hash"] = matchup_facts_hash
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True)
class RivalryChronicleGeneratedV1:
    text: str
    missing_weeks: tuple[int, ...]
    fingerprint: str
    anchor_week_index: int


def _resolve_team_name(db_path: str, league_id: int, season: int, franchise_id: str) -> str:
    """Resolve a franchise ID to its display name. Falls back to raw ID."""
    try:
        with DatabaseSession(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT name FROM franchise_directory "
                "WHERE league_id=? AND season=? AND franchise_id=? LIMIT 1",
                (str(league_id), int(season), str(franchise_id)),
            ).fetchone()
            if row and row["name"]:
                return str(row["name"]).strip()
    except Exception as exc:
        logger.debug("%s", exc)
        pass
    return str(franchise_id)


def generate_rivalry_chronicle_v1(
    *,
    db_path: str,
    league_id: int,
    season: int,
    week_indices: Sequence[int] | None,
    week_range: tuple[int, int] | None,
    missing_weeks_policy: MissingWeeksPolicy,
    created_at_utc: str,
    team_a_id: str | None = None,
    team_b_id: str | None = None,
) -> RivalryChronicleGeneratedV1:
    """Generate a rivalry chronicle from canonical matchup events.

    When team_a_id and team_b_id are provided (contract-compliant path):
    - Queries WEEKLY_MATCHUP_RESULT canonical events for the team pair
    - Builds a deterministic facts block with name resolution
    - Renders contract-compliant output structure

    When team args are omitted (legacy path):
    - Uses approved recap upstream quotes
    - Renders legacy provenance-based format
    """
    inp = RivalryChronicleInputV1(
        league_id=int(league_id),
        season=int(season),
        week_indices=tuple(week_indices) if week_indices is not None else None,
        week_range=(int(week_range[0]), int(week_range[1])) if week_range is not None else None,
        missing_weeks_policy=missing_weeks_policy,
    )

    def _approved_refs_loader(lid: int, yr: int, weeks: Sequence[int]) -> list:
        """Load approved recap references for chronicle generation."""
        return load_latest_approved_recap_refs_v1(
            db_path=db_path,
            league_id=lid,
            season=yr,
            artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP,
            week_indices=weeks,
        )

    resolver = ChronicleInputResolverV1(_approved_refs_loader)
    resolved = resolver.resolve(inp)

    missing = tuple(int(w) for w in resolved.missing_weeks)

    # ── Contract-compliant path (team pair provided) ──
    if team_a_id is not None and team_b_id is not None:
        matchup_facts = query_head_to_head_matchups_v1(
            db_path=db_path,
            league_id=str(league_id),
            season=int(season),
            team_a_id=str(team_a_id),
            team_b_id=str(team_b_id),
            week_indices=list(resolved.week_indices),
        )

        team_a_name = _resolve_team_name(db_path, league_id, season, str(team_a_id))
        team_b_name = _resolve_team_name(db_path, league_id, season, str(team_b_id))

        mf_hash = facts_block_hash_v1(matchup_facts)

        approved_recaps_tuple = tuple(
            (int(r.week_index), str(r.artifact_type), int(r.version), str(r.selection_fingerprint))
            for r in resolved.approved_recaps
        )
        fp = chronicle_fingerprint_v1(
            league_id=int(league_id),
            season=int(season),
            weeks_requested=resolved.week_indices,
            missing_weeks=missing,
            approved_recaps=approved_recaps_tuple,
            team_a_id=str(team_a_id),
            team_b_id=str(team_b_id),
            matchup_facts_hash=mf_hash,
        )

        # ── Creative Layer: governed narrative prose (optional) ──
        # Same pattern as weekly recaps: attempt LLM drafting constrained
        # by EAL, silent fallback on any failure. Narrative prose is NOT
        # part of the fingerprint — only deterministic facts matter.
        narrative_prose = None
        try:
            from squadvault.ai.creative_layer_rivalry_v1 import draft_rivalry_narrative_v1
            narrative_prose = draft_rivalry_narrative_v1(
                matchup_facts=matchup_facts,
                team_a_name=team_a_name,
                team_b_name=team_b_name,
                league_id=int(league_id),
                season=int(season),
            )
        except Exception as exc:
            logger.debug("%s", exc)
            pass

        out_text = render_rivalry_chronicle_contract_v1(
            league_id=int(league_id),
            season=int(season),
            team_a_id=str(team_a_id),
            team_b_id=str(team_b_id),
            team_a_name=team_a_name,
            team_b_name=team_b_name,
            week_indices_requested=resolved.week_indices,
            matchup_facts=matchup_facts,
            missing_weeks=missing,
            created_at_utc=created_at_utc,
            narrative_prose=narrative_prose,
        )

        anchor_week_index = int(max(resolved.week_indices))
        return RivalryChronicleGeneratedV1(
            text=out_text,
            missing_weeks=missing,
            fingerprint=fp,
            anchor_week_index=anchor_week_index,
        )

    # ── Legacy path (no team pair — upstream quotes) ──
    quotes: list[UpstreamRecapQuoteV1] = []
    for ref in resolved.approved_recaps:
        art = fetch_latest_approved_weekly_recap(
            db_path=db_path,
            league_id=str(resolved.league_id),
            season=int(resolved.season),
            week_index=int(ref.week_index),
            version=int(ref.version),
        )
        if art is None:
            continue

        quotes.append(
            UpstreamRecapQuoteV1(
                week_index=int(ref.week_index),
                artifact_type=str(ref.artifact_type),
                version=int(ref.version),
                selection_fingerprint=str(ref.selection_fingerprint),
                rendered_text=str(art.rendered_text or ""),
            )
        )

    out_text = render_rivalry_chronicle_v1(
        league_id=resolved.league_id,
        season=resolved.season,
        week_indices_requested=resolved.week_indices,
        upstream_quotes=quotes,
        missing_weeks=missing,
        created_at_utc=created_at_utc,
    )

    approved_recaps_tuple = tuple(
        (int(r.week_index), str(r.artifact_type), int(r.version), str(r.selection_fingerprint))
        for r in resolved.approved_recaps
    )
    fp = chronicle_fingerprint_v1(
        league_id=resolved.league_id,
        season=resolved.season,
        weeks_requested=resolved.week_indices,
        missing_weeks=missing,
        approved_recaps=approved_recaps_tuple,
    )
    anchor_week_index = int(max(resolved.week_indices))
    return RivalryChronicleGeneratedV1(text=out_text, missing_weeks=missing, fingerprint=fp, anchor_week_index=anchor_week_index)
