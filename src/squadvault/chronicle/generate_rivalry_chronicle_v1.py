# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT_CONTRACT_V1
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from squadvault.chronicle.approved_recap_refs_v1 import load_latest_approved_recap_refs_v1
from squadvault.chronicle.format_rivalry_chronicle_v1 import (
    UpstreamRecapQuoteV1,
    render_rivalry_chronicle_v1,
)
from squadvault.chronicle.input_contract_v1 import (
    ChronicleInputResolverV1,
    MissingWeeksPolicy,
    RivalryChronicleInputV1,
)
from squadvault.core.recaps.recap_artifacts import ARTIFACT_TYPE_WEEKLY_RECAP
from squadvault.core.exports.approved_weekly_recap_export_v1 import fetch_latest_approved_weekly_recap

ARTIFACT_TYPE_RIVALRY_CHRONICLE = "RIVALRY_CHRONICLE"

import hashlib
import json


def chronicle_fingerprint_v1(
    *,
    league_id: int,
    season: int,
    weeks_requested: Sequence[int],
    missing_weeks: Sequence[int],
    approved_recaps: Sequence[Tuple[int, str, int, str]],
) -> str:
    payload = {
        "chronicle_version": 1,
        "league_id": int(league_id),
        "season": int(season),
        "weeks_requested": list(weeks_requested),
        "missing_weeks": list(missing_weeks),
        # Each tuple: (week_index, artifact_type, version, selection_fingerprint)
        "approved_recaps": list(approved_recaps),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True)
class RivalryChronicleGeneratedV1:
    text: str
    missing_weeks: Tuple[int, ...]
    fingerprint: str
    anchor_week_index: int


def generate_rivalry_chronicle_v1(
    *,
    db_path: str,
    league_id: int,
    season: int,
    week_indices: Sequence[int] | None,
    week_range: Tuple[int, int] | None,
    missing_weeks_policy: MissingWeeksPolicy,
    created_at_utc: str,
) -> RivalryChronicleGeneratedV1:
    inp = RivalryChronicleInputV1(
        league_id=int(league_id),
        season=int(season),
        week_indices=tuple(week_indices) if week_indices is not None else None,
        week_range=tuple(week_range) if week_range is not None else None,
        missing_weeks_policy=missing_weeks_policy,
    )

    def _approved_refs_loader(lid: int, yr: int, weeks: Sequence[int]):
        return load_latest_approved_recap_refs_v1(
            db_path=db_path,
            league_id=lid,
            season=yr,
            artifact_type=ARTIFACT_TYPE_WEEKLY_RECAP,
            week_indices=weeks,
        )

    resolver = ChronicleInputResolverV1(_approved_refs_loader)
    resolved = resolver.resolve(inp)

    quotes: List[UpstreamRecapQuoteV1] = []
    for ref in resolved.approved_recaps:
        art = fetch_latest_approved_weekly_recap(
            db_path=db_path,
            league_id=str(resolved.league_id),
            season=int(resolved.season),
            week_index=int(ref.week_index),
            version=int(ref.version),
        )
        if art is None:
            # Defensive: should not happen. Treat as missing by omission.
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

    missing = tuple(int(w) for w in resolved.missing_weeks)

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
