"""Prompt Audit sidecar (v1 surface, v2 internals, rev3 map completion).

Captures one row per prompt attempt inside the Writing Room's `_generate_draft`
retry loop. Observation-only: never feeds back into facts, never alters drafts,
never gates publication. Presence is controlled by the environment variable
`SQUADVAULT_PROMPT_AUDIT=1`; anything else is a no-op.

v2 contract deltas (from the v1 delivery):
    * Signature takes `db_path: str`, not a `DatabaseSession` parameter. The
      audit hook opens a short-lived DatabaseSession internally via context
      manager (try/finally-semantic via __enter__/__exit__), so callers do not
      couple their session lifetime to audit writes.
    * No `version` argument. Schema versioning lives in the schema file name.
    * Append-only by structure: no UNIQUE constraint is relied upon; retries
      for the same (league_id, season, week, attempt) tuple are valid history.

rev3 delta (from rev2):
    * CATEGORY_TO_DETECTOR now covers all 50 D-attributable categories in the
      three canonical angle source files. Prior rev2 seed (32) was extended
      with the 18 keys surfaced by the drift detector test: the nine auction
      detectors (D20–D28) and the tail of Dimension 9 (D41–D48, D50).

Governing principles (per SquadVault constitution):
    * Facts are immutable and append-only — this table never updates rows.
    * Narratives are derived, never fact-creating — audit captures what the
      model saw and produced, it does not manufacture data.
    * Silence is preferred over speculation — when the env gate is off, the
      hook returns immediately and writes nothing.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import Any

from squadvault.core.storage.session import DatabaseSession

AUDIT_ENV_VAR = "SQUADVAULT_PROMPT_AUDIT"


# ---------------------------------------------------------------------------
# CATEGORY_TO_DETECTOR
#
# Maps narrative-angle `category` strings (as emitted by detector functions in
# squadvault.core.recaps.context) to their owning detector ID. Covers every
# D-attributable category present in the three canonical angle source files
# as of this rev. The drift detector test
# (test_category_to_detector_drift_detector) enforces continued completeness:
# when a new category appears in the codebase, the test fails loudly and this
# map must be extended.
#
# D4 (PLAYER_BOOM_BUST) and D49 (SCORING_MOMENTUM_IN_STREAK) are the explicit
# audit anchors for the current phase of observation. D41
# (TRANSACTION_VOLUME_IDENTITY) is included even though the detector is
# currently disabled in production — the category string still appears in
# source, so the map must cover it or the drift test rightly complains.
# ---------------------------------------------------------------------------
CATEGORY_TO_DETECTOR: dict[str, str] = {
    # Dimension 1 — current-season player scores (D1–D6)
    "PLAYER_HOT_STREAK": "D1",
    "PLAYER_COLD_STREAK": "D2",
    "PLAYER_SEASON_HIGH": "D3",
    "PLAYER_BOOM_BUST": "D4",
    "PLAYER_BREAKOUT": "D5",
    "ZERO_POINT_STARTER": "D6",
    # Dimension 2 — cross-season player lookups (D7–D11)
    "PLAYER_ALLTIME_HIGH": "D7",
    "PLAYER_FRANCHISE_RECORD": "D8",
    "CAREER_MILESTONE": "D9",
    "PLAYER_FRANCHISE_TENURE": "D10",
    "PLAYER_JOURNEY": "D11",
    # Dimension 3 — player × matchup (D12–D14)
    "PLAYER_VS_OPPONENT": "D12",
    "REVENGE_GAME": "D13",
    "PLAYER_DUEL": "D14",
    # Dimension 4 — trade & transaction outcomes (D15–D16)
    "TRADE_OUTCOME": "D15",
    "THE_ONE_THAT_GOT_AWAY": "D16",
    # Dimension 5 — FAAB & waiver efficiency (D17–D19)
    "FAAB_ROI_NOTABLE": "D17",
    "FAAB_FRANCHISE_EFFICIENCY": "D18",
    "WAIVER_DEPENDENCY": "D19",
    # Dimension 6 — auction draft outcomes (D20–D28)
    "AUCTION_PRICE_VS_PRODUCTION": "D20",
    "AUCTION_DOLLAR_PER_POINT": "D21",
    "AUCTION_BUST": "D22",
    "AUCTION_BUDGET_ALLOCATION": "D23",
    "AUCTION_POSITIONAL_SPENDING": "D24",
    "AUCTION_STRATEGY_CONSISTENCY": "D25",
    "AUCTION_LEAGUE_INFLATION": "D26",
    "AUCTION_DRAFT_TO_FAAB_PIPELINE": "D27",
    "AUCTION_MOST_EXPENSIVE_HISTORY": "D28",
    # Dimension 7 — franchise scoring patterns (D29–D32)
    "SCORING_CONCENTRATION": "D29",
    "SCORING_VOLATILITY": "D30",
    "STAR_EXPLOSION_COUNT": "D31",
    "POSITIONAL_STRENGTH": "D32",
    # Dimension 8 — bench & lineup decisions (D33–D35)
    "BENCH_COST_GAME": "D33",
    "CHRONIC_BENCH_MISMANAGEMENT": "D34",
    "PERFECT_LINEUP_WEEK": "D35",
    # Dimension 9 — franchise history & identity (D36–D50; D41 disabled)
    "CLOSE_GAME_RECORD": "D36",
    "SEASON_TRAJECTORY_MATCH": "D37",
    "SECOND_HALF_SURGE_COLLAPSE": "D38",
    "CHAMPIONSHIP_HISTORY": "D39",
    "FRANCHISE_ALLTIME_SCORING": "D40",
    "TRANSACTION_VOLUME_IDENTITY": "D41",  # detector disabled; category still attested
    "LUCKY_RECORD": "D42",
    "WEEKLY_SCORING_RANK_DOMINANCE": "D43",
    "SCHEDULE_STRENGTH": "D44",
    "REGULAR_SEASON_VS_PLAYOFF": "D45",
    "THE_BRIDESMAID": "D46",
    "POINTS_AGAINST_LUCK": "D47",
    "REPEAT_MATCHUP_PATTERN": "D48",
    "SCORING_MOMENTUM_IN_STREAK": "D49",
    "THE_ALMOST": "D50",
}


def _serialize(obj: Any) -> str:
    """Best-effort JSON serialization for heterogeneous angle/result payloads.

    Dataclasses are converted via asdict; anything else falls back to repr()
    so the audit row is written even when a payload contains non-JSON types.
    Audit fidelity > schema purity for an observation sidecar.
    """

    def _default(o: Any) -> Any:
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        if hasattr(o, "__dict__"):
            return {"__repr__": repr(o)}
        return repr(o)

    try:
        return json.dumps(obj, default=_default, sort_keys=True)
    except (TypeError, ValueError):
        return json.dumps({"__unserializable__": repr(obj)})


def _angles_summary(angles: Any) -> list[dict[str, Any]]:
    """Flatten an angle collection to a category-keyed summary list.

    We do not store full angle bodies (they can be large and they live in the
    canonical angle store already). We store enough to reconstruct which
    detectors fired at attempt time, which is the actual audit question.
    """
    out: list[dict[str, Any]] = []
    if angles is None:
        return out
    try:
        iterable = list(angles)
    except TypeError:
        return out
    for a in iterable:
        cat = getattr(a, "category", None)
        if cat is None and isinstance(a, dict):
            cat = a.get("category")
        if cat is None:
            continue
        out.append(
            {
                "category": cat,
                "detector": CATEGORY_TO_DETECTOR.get(cat, "UNMAPPED"),
            }
        )
    return out


def maybe_capture_attempt(
    db_path: str,
    *,
    league_id: str,
    season: int,
    week_index: int,
    attempt: int,
    all_angles: Any,
    budgeted: Any,
    narrative_angles_text: str,
    narrative_draft: str,
    verification_result: Any,
) -> None:
    """Capture one prompt attempt row if the audit env gate is enabled.

    No-op when SQUADVAULT_PROMPT_AUDIT is unset or not exactly "1". This
    avoids accidental auditing in CI / default local runs.

    Opens a short-lived DatabaseSession internally; the caller's session
    lifetime is not coupled to this write. Errors are swallowed silently —
    an observation sidecar must never block or mutate the draft pipeline.
    """
    if os.environ.get(AUDIT_ENV_VAR) != "1":
        return

    try:
        passed = bool(getattr(verification_result, "passed", False))
        row = (
            datetime.now(UTC).isoformat(),
            str(league_id),
            int(season),
            int(week_index),
            int(attempt),
            _serialize(_angles_summary(all_angles)),
            _serialize(_angles_summary(budgeted)),
            str(narrative_angles_text or ""),
            str(narrative_draft or ""),
            1 if passed else 0,
            _serialize(verification_result),
        )
        with DatabaseSession(db_path) as con:
            con.execute(
                """
                INSERT INTO prompt_audit (
                    captured_at,
                    league_id,
                    season,
                    week_index,
                    attempt,
                    angles_summary_json,
                    budgeted_summary_json,
                    narrative_angles_text,
                    narrative_draft,
                    verification_passed,
                    verification_result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
    except Exception:
        # Observation sidecar: never raise out of the audit path.
        return
