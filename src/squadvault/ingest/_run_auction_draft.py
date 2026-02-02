import json

from squadvault.ingest.auction_draft import (
    derive_auction_event_envelopes_from_transactions,
)

# TEMPORARY hardcoded values
YEAR = 2024
LEAGUE_ID = "TEST_LEAGUE"
SOURCE_URL = "https://www.myfantasyleague.com"

# TEMPORARY fake transaction (replace later with real API data)
FAKE_TRANSACTIONS = [
    {
        "type": "AUCTION_WON",
        "timestamp": "1693527600",  # unix seconds as string (example)
        "franchise": "0001",
        "player": "12345",
        "amount": "27",
    }
]

events = derive_auction_event_envelopes_from_transactions(
    year=YEAR,
    league_id=LEAGUE_ID,
    transactions=FAKE_TRANSACTIONS,
    source_url=SOURCE_URL,
)

print(json.dumps(events, indent=2))
