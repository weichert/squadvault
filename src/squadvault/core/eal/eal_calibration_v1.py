"""
SquadVault — EAL Calibration (Type A) v1

Contract: docs/30_contract_cards/ops/EAL_CALIBRATION_Contract_Card_v1.0.docx

Type A scope:
- schema validation for calibration records
- deterministic selection of effective calibration (most recent approved_at among valid)
- conservative, fail-closed restraint directive derivation
- reproducible directive fingerprinting

Not in Type A:
- authority enforcement (founder/delegation)
- persistence / DB / window immutability integration
- audit logging plumbing
- safety-system override wiring

Default: any behavior not explicitly permitted is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_CALIBRATION_VALUES: Dict[str, Any] = {
    "min_signal_count_for_confidence": 3,
    "max_ambiguity_tolerance": 0.25,
    "max_grouping_density": 0.5,
}


class RestraintDirective(Enum):
    high_restraint = "high_restraint"
    moderate_restraint = "moderate_restraint"
    neutral = "neutral"
    prefer_silence = "prefer_silence"


@dataclass(frozen=True)
class EALRestraintDirectiveV1:
    restraint_directive: str
    window_id: str
    source_calibration_id: str
    directive_fingerprint: str
    generated_at: str  # ISO-8601 UTC timestamp


def _is_nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and x.strip() != ""


def _parse_iso8601_utc(ts: Any) -> Optional[datetime]:
    """
    Strict-ish: must parse and include tzinfo, and must be UTC offset.
    Accepts "+00:00" and "Z".
    """
    if not isinstance(ts, str) or ts.strip() == "":
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        return None
    # Require UTC offset
    off = dt.utcoffset()
    if off is None or off.total_seconds() != 0:
        return None
    return dt


def _is_semver_like(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    parts = v.strip().split(".")
    if len(parts) < 3:
        return False
    try:
        int(parts[0]); int(parts[1]); int(parts[2])
        return True
    except Exception:
        return False


def validate_calibration_schema(cal: Dict[str, Any]) -> List[str]:
    errs: List[str] = []

    required = [
        "calibration_id",
        "scope",
        "min_signal_count_for_confidence",
        "max_ambiguity_tolerance",
        "max_grouping_density",
        "version",
        "approved_by",
        "approved_at",
    ]
    optional = {"scope_id", "supersedes"}

    for k in required:
        if k not in cal:
            errs.append(f"missing required field: {k}")

    for k in cal.keys():
        if k not in set(required) | optional:
            errs.append(f"unexpected field: {k}")

    if "calibration_id" in cal and not _is_nonempty_str(cal["calibration_id"]):
        errs.append("calibration_id must be non-empty string")

    if "scope" in cal:
        if cal["scope"] not in ("system", "group"):
            errs.append("scope invalid (expected enum[system, group])")

    if cal.get("scope") == "group":
        if not _is_nonempty_str(cal.get("scope_id")):
            errs.append("scope_id required for group scope and must be non-empty string")

    if "min_signal_count_for_confidence" in cal:
        v = cal["min_signal_count_for_confidence"]
        if not isinstance(v, int):
            errs.append("min_signal_count_for_confidence must be integer")
        elif v < 1:
            errs.append("min_signal_count_for_confidence must be >= 1")

    for fk in ("max_ambiguity_tolerance", "max_grouping_density"):
        if fk in cal:
            v = cal[fk]
            if not isinstance(v, (int, float)):
                errs.append(f"{fk} must be float (0.0–1.0)")
            else:
                fv = float(v)
                if fv < 0.0 or fv > 1.0:
                    errs.append(f"{fk} out of range (expected 0.0–1.0)")

    if "version" in cal and not _is_semver_like(cal["version"]):
        errs.append("version must be semver-like string (e.g. 1.0.0)")

    if "approved_by" in cal and not _is_nonempty_str(cal["approved_by"]):
        errs.append("approved_by must be non-empty string")

    if "approved_at" in cal:
        if _parse_iso8601_utc(cal["approved_at"]) is None:
            errs.append("approved_at must be ISO-8601 UTC timestamp")

    for lk in ("supersedes", "scope_id"):
        if lk in cal and cal[lk] is not None and not _is_nonempty_str(cal[lk]):
            errs.append(f"{lk} must be optional<non-empty string>")

    return errs


def default_system_calibration_record() -> Dict[str, Any]:
    # We provide a deterministic default record for Type A behavior.
    # calibration_id is fixed to avoid entropy in fingerprints.
    return {
        "calibration_id": "default_system_calibration_v1",
        "scope": "system",
        "scope_id": None,
        "min_signal_count_for_confidence": int(DEFAULT_CALIBRATION_VALUES["min_signal_count_for_confidence"]),
        "max_ambiguity_tolerance": float(DEFAULT_CALIBRATION_VALUES["max_ambiguity_tolerance"]),
        "max_grouping_density": float(DEFAULT_CALIBRATION_VALUES["max_grouping_density"]),
        "version": "1.0.0",
        "approved_by": "system_default",
        "approved_at": "1970-01-01T00:00:00+00:00",
        "supersedes": None,
    }


def select_effective_calibration(
    calibrations: List[Dict[str, Any]],
    *,
    scope: str,
    scope_id: Optional[str],
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Type A selection semantics:
    - Filter by (scope, scope_id) (scope_id required for group).
    - Consider only schema-valid calibrations.
    - Select most recently approved by approved_at timestamp.
    - If none valid, return default system calibration.
    - If ambiguity exists (multiple valid), return latest and include warning.
    """
    warnings: List[str] = []

    if scope not in ("system", "group"):
        # Fail closed.
        warnings.append("invalid scope requested; using default calibration")
        return default_system_calibration_record(), warnings

    if scope == "group" and not _is_nonempty_str(scope_id):
        warnings.append("group scope without scope_id; using default calibration")
        return default_system_calibration_record(), warnings

    candidates: List[Dict[str, Any]] = []
    rejected_invalid = 0
    for c in calibrations:
        if not isinstance(c, dict):
            continue
        if c.get("scope") != scope:
            continue
        if scope == "group" and c.get("scope_id") != scope_id:
            continue
        if scope == "system" and c.get("scope_id") not in (None, "",):
            # system scope should not carry scope_id; treat as invalid
            pass
        if validate_calibration_schema(c):
            rejected_invalid += 1
            continue
        candidates.append(c)

    if rejected_invalid > 0:
        warnings.append("invalid calibration values rejected")

    if not candidates:
        warnings.append("no valid calibration found; using default calibration")
        return default_system_calibration_record(), warnings

    # Deterministic latest-by-approved_at selection (ties broken by calibration_id).
    def _key(c: Dict[str, Any]) -> Tuple[datetime, str]:
        dt = _parse_iso8601_utc(c["approved_at"])
        assert dt is not None
        return (dt, str(c.get("calibration_id", "")))

    candidates_sorted = sorted(candidates, key=_key)
    chosen = candidates_sorted[-1]

    if len(candidates_sorted) > 1:
        warnings.append("conflicting active calibrations; selected most recently approved")

    return chosen, warnings


def derive_restraint_directive(
    *,
    window_id: str,
    signal_count: Optional[int],
    ambiguity: Optional[float],
    grouping_density: Optional[float],
    calibration: Optional[Dict[str, Any]],
) -> RestraintDirective:
    """
    Minimal conservative derivation (Type A):
    - If any uncertainty / missing inputs -> prefer_silence.
    - Enforce thresholds strictly.
    - If thresholds satisfied, still return high_restraint (contract does not define
      a path to neutral/moderate without adding policy).
    """
    # Fail closed on missing required context.
    if not _is_nonempty_str(window_id):
        return RestraintDirective.prefer_silence

    if calibration is None or validate_calibration_schema(calibration):
        # Missing or invalid calibration -> default baseline, but maximum restraint.
        # Contract: "Absence of calibration defaults to maximum restraint"
        return RestraintDirective.prefer_silence

    if signal_count is None or not isinstance(signal_count, int):
        return RestraintDirective.prefer_silence
    if ambiguity is None or not isinstance(ambiguity, (int, float)):
        return RestraintDirective.prefer_silence
    if grouping_density is None or not isinstance(grouping_density, (int, float)):
        return RestraintDirective.prefer_silence

    min_sig = int(calibration["min_signal_count_for_confidence"])
    max_amb = float(calibration["max_ambiguity_tolerance"])
    max_den = float(calibration["max_grouping_density"])

    if signal_count < min_sig:
        return RestraintDirective.prefer_silence
    if float(ambiguity) > max_amb:
        return RestraintDirective.prefer_silence
    if float(grouping_density) > max_den:
        return RestraintDirective.prefer_silence

    return RestraintDirective.high_restraint


def _canonical_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_directive_fingerprint(
    *,
    window_id: str,
    source_calibration_id: str,
    restraint_directive: str,
    inputs: Dict[str, Any],
) -> str:
    """
    Contract requires reproducibility but does not specify a formula.
    We define an explicit, deterministic Type A fingerprint:
      sha256(window_id + "|" + source_calibration_id + "|" + restraint_directive + "|" + canonical_json(inputs))
    """
    base = (
        f"{window_id}|{source_calibration_id}|{restraint_directive}|{_canonical_json(inputs)}"
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def build_restraint_directive_v1(
    *,
    window_id: str,
    signal_count: Optional[int],
    ambiguity: Optional[float],
    grouping_density: Optional[float],
    calibration: Optional[Dict[str, Any]],
    generated_at: Optional[str] = None,
) -> EALRestraintDirectiveV1:
    """
    Construct the derived directive record (non-canonical output).
    """
    if generated_at is None:
        # Deterministic timestamping is not required in Type A tests.
        # Use real UTC time, but tests should pass explicit generated_at.
        generated_at = datetime.now(timezone.utc).isoformat()

    rd = derive_restraint_directive(
        window_id=window_id,
        signal_count=signal_count,
        ambiguity=ambiguity,
        grouping_density=grouping_density,
        calibration=calibration,
    )

    source_id = (
        calibration["calibration_id"]
        if isinstance(calibration, dict) and "calibration_id" in calibration and not validate_calibration_schema(calibration)
        else default_system_calibration_record()["calibration_id"]
    )

    inputs = {
        "signal_count": signal_count,
        "ambiguity": float(ambiguity) if isinstance(ambiguity, (int, float)) else ambiguity,
        "grouping_density": float(grouping_density) if isinstance(grouping_density, (int, float)) else grouping_density,
        "calibration_id": source_id,
    }

    fp = compute_directive_fingerprint(
        window_id=window_id,
        source_calibration_id=source_id,
        restraint_directive=rd.value,
        inputs=inputs,
    )

    return EALRestraintDirectiveV1(
        restraint_directive=rd.value,
        window_id=window_id,
        source_calibration_id=source_id,
        directive_fingerprint=fp,
        generated_at=generated_at,
    )
