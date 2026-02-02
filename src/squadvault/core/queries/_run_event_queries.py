import os
from pathlib import Path

from dotenv import load_dotenv

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.queries.event_queries import (
    draft_picks,
    waiver_awards,
    waiver_requests,
    trades,
    free_agent_transactions,
)

load_dotenv(".env")

DB_PATH = Path(".local_squadvault.sqlite")
LEAGUE_ID = os.environ["MFL_LEAGUE_ID"]
SEASON = int(os.environ.get("SQUADVAULT_YEAR", "2024"))

store = SQLiteStore(DB_PATH)

print("draft_picks=", len(draft_picks(store, league_id=LEAGUE_ID, season=SEASON)))
print("waiver_requests=", len(waiver_requests(store, league_id=LEAGUE_ID, season=SEASON)))
print("waiver_awards=", len(waiver_awards(store, league_id=LEAGUE_ID, season=SEASON)))
print("trades=", len(trades(store, league_id=LEAGUE_ID, season=SEASON)))
print("free_agent_transactions=", len(free_agent_transactions(store, league_id=LEAGUE_ID, season=SEASON)))

