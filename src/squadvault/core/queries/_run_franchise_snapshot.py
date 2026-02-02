import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.queries.franchise_queries import (
    draft_picks_for_franchise,
    waiver_awards_for_franchise,
    free_agent_moves_for_franchise,
    trades_for_franchise,
)

load_dotenv(".env")

DB_PATH = Path(".local_squadvault.sqlite")
LEAGUE_ID = os.environ["MFL_LEAGUE_ID"]
SEASON = int(os.environ.get("SQUADVAULT_YEAR", "2024"))

# Change this to any franchise in your league, e.g. "0001"
FRANCHISE_ID = os.environ.get("SQUADVAULT_FRANCHISE_ID", "0001")

store = SQLiteStore(DB_PATH)

draft = draft_picks_for_franchise(store, league_id=LEAGUE_ID, season=SEASON, franchise_id=FRANCHISE_ID)
waivers = waiver_awards_for_franchise(store, league_id=LEAGUE_ID, season=SEASON, franchise_id=FRANCHISE_ID)
fa = free_agent_moves_for_franchise(store, league_id=LEAGUE_ID, season=SEASON, franchise_id=FRANCHISE_ID)
trades = trades_for_franchise(store, league_id=LEAGUE_ID, season=SEASON, franchise_id=FRANCHISE_ID)


def _score_waiver_award(e: Dict[str, Any]) -> Tuple[int, str]:
    """
    Prefer waiver award events that have richer parsed payload fields.
    Score:
      +1 if bid_amount is not None
      +1 if player_id is non-empty
    Tie-breaker: most recent ingested_at.
    """
    p = e.get("payload") or {}
    bid_ok = p.get("bid_amount") is not None
    pid_ok = bool((p.get("player_id") or "").strip())
    score = (1 if bid_ok else 0) + (1 if pid_ok else 0)
    ingested_at = e.get("ingested_at") or ""
    return score, ingested_at


def best_waiver_award(events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not events:
        return None
    return sorted(events, key=_score_waiver_award, reverse=True)[0]


print("franchise_id=", FRANCHISE_ID)
print("draft_picks=", len(draft))
print("waiver_awards=", len(waivers))
print("free_agent_moves=", len(fa))
print("trades=", len(trades))

# Print one sample of each if present (prefer "best" waiver award)
if draft:
    print("sample_draft_pick=", draft[0])

best_waiver = best_waiver_award(waivers)
if best_waiver:
    print("sample_waiver_award=", best_waiver)

if fa:
    print("sample_free_agent=", fa[0])

if trades:
    print("sample_trade=", trades[0])



