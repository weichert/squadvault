"""Recap event allowlist — which event_types produce recap bullets."""

# Recap-relevant "human moves"
INCLUDE_EVENT_TYPES = {
    "TRANSACTION_TRADE",
    "TRANSACTION_FREE_AGENT",
    "TRANSACTION_WAIVER",
    "TRANSACTION_BBID_WAIVER",
    "WAIVER_BID_AWARDED",
    "TRANSACTION_AUCTION_WON",  # include if it represents a player acquisition
}

# Ops / noise / boundaries / non-story
EXCLUDE_EVENT_TYPES = {
    "DRAFT_PICK",  # unless explicitly generating "Draft Week" recaps
    "TRANSACTION_LOCK_ALL_PLAYERS",  # boundary marker only
    "TRANSACTION_AUTO_PROCESS_WAIVERS",  # ops
    "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS",  # ops
}
