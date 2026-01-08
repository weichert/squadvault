import os
from pathlib import Path
from collections import Counter

from dotenv import load_dotenv

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.queries.event_queries import fetch_all_events
from squadvault.core.queries.narrative_filters import filter_events_for_narrative

load_dotenv(".env")

DB_PATH = Path(".local_squadvault.sqlite")
LEAGUE_ID = os.environ["MFL_LEAGUE_ID"]
SEASON = int(os.environ.get("SQUADVAULT_YEAR", "2024"))

store = SQLiteStore(DB_PATH)

all_events = fetch_all_events(store, league_id=LEAGUE_ID, season=SEASON, limit=10000)
narrative = filter_events_for_narrative(all_events)

counts = Counter([e["event_type"] for e in narrative])

print("all_events=", len(all_events))
print("narrative_events=", len(narrative))
print("narrative_by_type=", dict(counts))


