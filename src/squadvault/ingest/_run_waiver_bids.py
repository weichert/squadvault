import json

from squadvault.ingest.waiver_bids import derive_waiver_bid_event_envelopes_from_transactions

YEAR = 2024
LEAGUE_ID = "TEST_LEAGUE"
SOURCE_URL = "https://www.myfantasyleague.com"

FAKE_TRANSACTIONS = [
    {
        "type": "BBID_WAIVER_REQUEST",
        "timestamp": "1693527600",
        "franchise": "0001",
        "player": "77777",
        "bid": "13",
    },
    {
        "type": "BBID_WAIVER",
        "timestamp": "1693531200",
        "franchise": "0001",
        "player": "77777",
        "bid": "13",
    },
]

events = derive_waiver_bid_event_envelopes_from_transactions(
    year=YEAR,
    league_id=LEAGUE_ID,
    transactions=FAKE_TRANSACTIONS,
    source_url=SOURCE_URL,
)

print(json.dumps(events, indent=2))