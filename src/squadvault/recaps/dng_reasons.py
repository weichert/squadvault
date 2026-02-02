# src/squadvault/recaps/dng_reasons.py
from __future__ import annotations

from enum import Enum


class DNGReason(str, Enum):
    DNG_INCOMPLETE_WEEK = "DNG_INCOMPLETE_WEEK"
    DNG_DATA_GAP_DETECTED = "DNG_DATA_GAP_DETECTED"
    DNG_LOW_TRUST_OUTPUT_RISK = "DNG_LOW_TRUST_OUTPUT_RISK"
    DNG_SAFETY_CONFLICT = "DNG_SAFETY_CONFLICT"
    DNG_OUT_OF_SCOPE_REQUEST = "DNG_OUT_OF_SCOPE_REQUEST"
