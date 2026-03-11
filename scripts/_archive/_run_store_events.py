from pathlib import Path

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.auction_draft import derive_auction_event_envelopes_from_transactions

SCHEMA = Path("src/squadvault/core/storage/schema.sql").read_text()
DB_PATH = Path(".local_squadvault.sqlite")

store = SQLiteStore(DB_PATH)
store.init_db(SCHEMA)

events = derive_auction_event_envelopes_from_transactions(
    year=2024,
    league_id="TEST_LEAGUE",
    transactions=[
        {"type": "AUCTION_WON", "timestamp": "1693527600", "franchise": "0001", "player": "12345", "amount": "27"}
    ],
    source_url="https://www.myfantasyleague.com",
)

inserted, skipped = store.append_events(events)
print("inserted=", inserted, "skipped=", skipped)

fetched = store.fetch_events(league_id="TEST_LEAGUE", season=2024)
print("fetched=", len(fetched))
print(fetched[0])