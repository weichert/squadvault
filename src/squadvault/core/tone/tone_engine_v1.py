"""
SquadVault — Tone Engine (Type A scaffolding) v1

Contract: Tone Engine Contract Card v1.0 (canonical .docx)
Inspection surface: docs/contracts/tier_2/tone_engine/_extracted_txt/tone_engine_contract_v1.0.txt

Type A scope:
- Pure schema validation (config)
- Deterministic directive derivation
- Default neutral configuration
- Canonical directive fingerprint calculation
- Conflict selection rule (most recent approved_at) as pure function returning warnings

Default: Any behavior not explicitly permitted by the contract is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


class FormalityLevel(str, Enum):
    casual = "casual"
    balanced = "balanced"
    formal = "formal"


class CeremonialWeight(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class FormalityConstraint(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class HumorConstraint(str, Enum):
    none = "none"
    light = "light"
    moderate = "moderate"


class ProfanityConstraint(str, Enum):
    forbidden = "forbidden"
    permitted = "permitted"


class CeremonialEmphasis(str, Enum):
    none = "none"
    restrained = "restrained"
    elevated = "elevated"


class ToneDirectiveStatus(str, Enum):
    ok = "ok"
    error = "error"


@dataclass(frozen=True)
class ToneDirectiveV1:
    group_id: str
    window_id: str
    source_tone_config_id: str
    formality_constraint: str
    humor_constraint: str
    profanity_constraint: str
    ceremonial_emphasis: str
    directive_fingerprint: str


DEFAULT_NEUTRAL_CONFIG_V1: Dict[str, Any] = {
    "tone_config_id": "default-neutral",
    "group_id": "__unset__",  # filled at use-time
    "formality_level": FormalityLevel.balanced.value,
    "humor_permitted": False,
    "profanity_permitted": False,
    "ceremonial_weight": CeremonialWeight.low.value,
    "approved_at": "1970-01-01T00:00:00+00:00",
}


def _parse_iso8601_utc(ts: str) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts.strip():
        return None
    s = ts.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            return None
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc
    except Exception:
        return None


def validate_tone_config_schema_v1(cfg: Dict[str, Any]) -> List[str]:
    """
    Type A: strict validation (fail closed). No coercion.
    Only validates fields required for Type A derivation + ordering.
    """
    errs: List[str] = []
    if not isinstance(cfg, dict):
        return ["tone config must be a dict"]

    def req(name: str, typ: Any) -> Any:
        if name not in cfg:
            errs.append(f"missing required field: {name}")
            return None
        val = cfg.get(name)
        if typ is not None and not isinstance(val, typ):
            errs.append(f"field {name} must be {typ.__name__}")
            return None
        return val

    tone_config_id = req("tone_config_id", str)
    group_id = req("group_id", str)
    formality_level = req("formality_level", str)
    humor_permitted = req("humor_permitted", bool)
    profanity_permitted = req("profanity_permitted", bool)
    ceremonial_weight = req("ceremonial_weight", str)
    approved_at = req("approved_at", str)

    if tone_config_id is not None and not tone_config_id.strip():
        errs.append("tone_config_id must be non-empty string")
    if group_id is not None and not group_id.strip():
        errs.append("group_id must be non-empty string")

    if formality_level is not None and formality_level not in {e.value for e in FormalityLevel}:
        errs.append(f"formality_level invalid: {formality_level}")

    if ceremonial_weight is not None and ceremonial_weight not in {e.value for e in CeremonialWeight}:
        errs.append(f"ceremonial_weight invalid: {ceremonial_weight}")

    if approved_at is not None:
        dt = _parse_iso8601_utc(approved_at)
        if dt is None:
            errs.append("approved_at must be ISO-8601 UTC timestamp")

    supersedes = cfg.get("supersedes")
    if supersedes is not None and not isinstance(supersedes, str):
        errs.append("supersedes must be tone_config_id string or null")

    return errs


def _map_formality(level: str) -> str:
    # deterministic mapping
    if level == FormalityLevel.casual.value:
        return FormalityConstraint.low.value
    if level == FormalityLevel.balanced.value:
        return FormalityConstraint.medium.value
    if level == FormalityLevel.formal.value:
        return FormalityConstraint.high.value
    # validation should catch this; fail closed fallback:
    return FormalityConstraint.medium.value


def _map_humor(permitted: bool) -> str:
    return HumorConstraint.light.value if permitted else HumorConstraint.none.value


def _map_profanity(permitted: bool) -> str:
    return ProfanityConstraint.permitted.value if permitted else ProfanityConstraint.forbidden.value


def _map_ceremonial(weight: str, *, artifact_class_is_ceremonial: bool) -> str:
    # hard invariant: if not ceremonial class -> "none" regardless of weight
    if not artifact_class_is_ceremonial:
        return CeremonialEmphasis.none.value

    if weight == CeremonialWeight.low.value:
        return CeremonialEmphasis.restrained.value
    if weight == CeremonialWeight.medium.value:
        return CeremonialEmphasis.restrained.value
    if weight == CeremonialWeight.high.value:
        return CeremonialEmphasis.elevated.value
    # validation should catch; fail closed:
    return CeremonialEmphasis.none.value


def derive_directive_values_v1(cfg: Dict[str, Any], *, artifact_class_is_ceremonial: bool) -> Dict[str, Any]:
    """
    Type A: pure derivation from config only.
    Returns directive_values object used in fingerprint calculation.
    """
    return {
        "formality_constraint": _map_formality(cfg["formality_level"]),
        "humor_constraint": _map_humor(cfg["humor_permitted"]),
        "profanity_constraint": _map_profanity(cfg["profanity_permitted"]),
        "ceremonial_emphasis": _map_ceremonial(cfg["ceremonial_weight"], artifact_class_is_ceremonial=artifact_class_is_ceremonial),
    }


def compute_directive_fingerprint_v1(
    *,
    group_id: str,
    window_id: str,
    source_tone_config_id: str,
    directive_values: Dict[str, Any],
) -> str:
    """
    Canonical fingerprint:
      sha256(group_id + "|" + window_id + "|" + source_tone_config_id + "|" + JSON.stringify(directive_values, sorted_keys=true))
    """
    payload = (
        f"{group_id}|"
        f"{window_id}|"
        f"{source_tone_config_id}|"
        + json.dumps(directive_values, sort_keys=True, separators=(",", ":"))
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def select_effective_tone_config_v1(configs: Optional[List[Dict[str, Any]]], *, group_id: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """
    Type A selection semantics:
    - If no config exists: use Default Neutral Configuration.
    - If multiple configs provided: choose most recent approved_at timestamp; emit warning.
    - If selected config invalid: return errors (caller fails closed).
    """
    errs: List[str] = []
    warnings: List[str] = []

    if not configs:
        cfg = dict(DEFAULT_NEUTRAL_CONFIG_V1)
        cfg["group_id"] = group_id
        return cfg, errs, warnings

    # validate each candidate's approved_at parseability for ordering; fail closed if missing/invalid
    parsed: List[Tuple[datetime, Dict[str, Any]]] = []
    for i, c in enumerate(configs):
        if not isinstance(c, dict):
            errs.append(f"configs[{i}] must be dict")
            continue
        ts = c.get("approved_at")
        dt = _parse_iso8601_utc(ts) if isinstance(ts, str) else None
        if dt is None:
            errs.append(f"configs[{i}].approved_at invalid or missing")
            continue
        parsed.append((dt, c))

    if errs:
        # cannot safely select
        cfg = dict(DEFAULT_NEUTRAL_CONFIG_V1)
        cfg["group_id"] = group_id
        return cfg, errs, warnings

    parsed.sort(key=lambda t: t[0])
    if len(parsed) > 1:
        warnings.append("conflicting active configurations: selected most recent approved_at")

    return parsed[-1][1], errs, warnings


def build_tone_directive_v1(
    *,
    group_id: str,
    window_id: str,
    configs: Optional[List[Dict[str, Any]]],
    artifact_class_is_ceremonial: bool,
) -> Tuple[Optional[ToneDirectiveV1], ToneDirectiveStatus, Optional[str], List[str]]:
    """
    Type A builder:
    - Select effective config (default neutral or most recent).
    - Validate selected config schema; fail closed on errors.
    - Derive directive values deterministically.
    - Compute canonical fingerprint deterministically.
    """
    cfg, select_errs, warnings = select_effective_tone_config_v1(configs, group_id=group_id)
    if select_errs:
        return None, ToneDirectiveStatus.error, "; ".join(select_errs), warnings

    schema_errs = validate_tone_config_schema_v1(cfg)
    if schema_errs:
        return None, ToneDirectiveStatus.error, "; ".join(schema_errs), warnings

    directive_values = derive_directive_values_v1(cfg, artifact_class_is_ceremonial=artifact_class_is_ceremonial)
    fp = compute_directive_fingerprint_v1(
        group_id=group_id,
        window_id=window_id,
        source_tone_config_id=cfg["tone_config_id"],
        directive_values=directive_values,
    )

    d = ToneDirectiveV1(
        group_id=group_id,
        window_id=window_id,
        source_tone_config_id=cfg["tone_config_id"],
        formality_constraint=directive_values["formality_constraint"],
        humor_constraint=directive_values["humor_constraint"],
        profanity_constraint=directive_values["profanity_constraint"],
        ceremonial_emphasis=directive_values["ceremonial_emphasis"],
        directive_fingerprint=fp,
    )
    return d, ToneDirectiveStatus.ok, None, warnings
