from __future__ import annotations

from enum import Enum


class PlayStyle(Enum):
    CONSERVATIVE = "CONSERVATIVE"
    AGGRESSIVE = "AGGRESSIVE"
    BALANCED = "BALANCED"
    TRICKY = "TRICKY"


class PublicationMode(Enum):
    AUTO = "AUTO"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HOLD = "HOLD"