import json

from squadvault.ingest.transactions import derive_transaction_event_envelopes

YEAR = 2024
LEAGUE_ID = "TEST_LEAGUE"
SOURCE_URL = "https://www.myfantasyleague.com"

FAKE_TRANSACTIONS = [
    {
        "type": "ADD",
        "timestamp": "1693527600",
        "franchise": "0001",
        "player": "54321",
    }
]

events = derive_transaction_event_envelopes(
    year=YEAR,
    league_id=LEAGUE_ID,
    transactions=FAKE_TRANSACTIONS,
    source_url=SOURCE_URL,
)

print(json.dumps(events, indent=2))
