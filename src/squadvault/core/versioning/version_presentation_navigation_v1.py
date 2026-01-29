"""
SquadVault — Version Presentation & Navigation (Type A scaffolding) v1

Contract: VERSION_PRESENTATION_NAVIGATION_Contract_Card_v1.0

Scope (Type A only):
- Pure validation + deterministic ordering + lossless navigation helpers.
- Fail closed on ambiguity.
- No DB I/O, no UI behavior, no heuristics, no recommendations.

Default: Any behavior not explicitly permitted by the contract is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple


class CreatedBy(str, Enum):
    system = "system"
    regeneration = "regeneration"
    human_edit = "human_edit"


class CreationReason(str, Enum):
    initial = "initial"
    late_data = "late_data"
    tone_change = "tone_change"
    correction = "correction"
    annotation = "annotation"


class ApprovalStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    withheld = "withheld"


class PresentationStatus(str, Enum):
    ok = "ok"
    withheld = "withheld"
    error = "error"


@dataclass(frozen=True)
class PresentationIndexV1:
    versions: List[Dict[str, Any]]
    canonical_version_id: Optional[str]
    status: PresentationStatus
    integrity_violations: List[str]
    error: Optional[str]


def _parse_iso8601_utc(ts: str) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        s = ts.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            return None
        dt_utc = dt.astimezone(timezone.utc)
        if dt_utc.utcoffset() != timezone.utc.utcoffset(dt_utc):
            return None
        return dt_utc
    except Exception:
        return None


def _is_sha256ish(s: str) -> bool:
    if not isinstance(s, str) or len(s) != 64:
        return False
    return all(c in "0123456789abcdef" for c in s.lower())


def validate_version_metadata_schema(v: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if not isinstance(v, dict):
        return ["version metadata must be a dict"]

    def req(name: str, typ: Any) -> Any:
        if name not in v:
            errs.append(f"missing required field: {name}")
            return None
        val = v.get(name)
        if typ is not None and not isinstance(val, typ):
            errs.append(f"field {name} must be {typ.__name__}")
            return None
        return val

    artifact_id = req("artifact_id", str)
    version_id = req("version_id", str)
    version_number = req("version_number", int)
    created_at = req("created_at", str)
    created_by = req("created_by", str)
    creation_reason = req("creation_reason", str)
    approval_status = req("approval_status", str)
    _is_canonical = req("is_canonical", bool)
    window_id = req("window_id", str)
    fingerprint = req("fingerprint", str)

    supersedes = v.get("supersedes")
    superseded_by = v.get("superseded_by")

    if artifact_id is not None and not artifact_id.strip():
        errs.append("artifact_id must be non-empty")

    if version_id is not None and not version_id.strip():
        errs.append("version_id must be non-empty string")

    if version_number is not None and version_number < 0:
        errs.append("version_number must be >= 0")

    if created_at is not None:
        dt = _parse_iso8601_utc(created_at)
        if dt is None:
            errs.append("created_at must be ISO-8601 UTC timestamp")

    if created_by is not None and created_by not in {e.value for e in CreatedBy}:
        errs.append(f"created_by invalid: {created_by}")

    if creation_reason is not None and creation_reason not in {e.value for e in CreationReason}:
        errs.append(f"creation_reason invalid: {creation_reason}")

    if approval_status is not None and approval_status not in {e.value for e in ApprovalStatus}:
        errs.append(f"approval_status invalid: {approval_status}")

    if window_id is not None and not window_id.strip():
        errs.append("window_id must be non-empty")

    if fingerprint is not None and not _is_sha256ish(fingerprint):
        errs.append("fingerprint must be sha256 hex string")

    if supersedes is not None and not isinstance(supersedes, str):
        errs.append("supersedes must be version_id string or null")
    if superseded_by is not None and not isinstance(superseded_by, str):
        errs.append("superseded_by must be version_id string or null")

    if supersedes is not None and supersedes == version_id:
        errs.append("supersedes must not self-reference")
    if superseded_by is not None and superseded_by == version_id:
        errs.append("superseded_by must not self-reference")

    return errs


def validate_version_set_schema(versions: Iterable[Dict[str, Any]]) -> List[str]:
    if versions is None:
        return ["versions must be provided"]
    if not isinstance(versions, list):
        return ["versions must be a list of dicts"]
    errs: List[str] = []
    for i, v in enumerate(versions):
        for e in validate_version_metadata_schema(v):
            errs.append(f"versions[{i}]: {e}")
    return errs


def validate_canonical_constraints(versions: List[Dict[str, Any]]) -> List[str]:
    errs: List[str] = []
    canonical = [v for v in versions if v.get("is_canonical") is True]
    if len(canonical) > 1:
        errs.append("ambiguous canonical: more than one version has is_canonical=true")

    for v in versions:
        if v.get("is_canonical") is True:
            if v.get("approval_status") != ApprovalStatus.approved.value:
                errs.append("canonical version must be approval_status=approved")
            if v.get("superseded_by") is not None:
                errs.append("canonical version must not have superseded_by set")

        if v.get("approval_status") in {ApprovalStatus.draft.value, ApprovalStatus.withheld.value}:
            if v.get("is_canonical") is True:
                errs.append("draft/withheld versions may never be canonical")

        if v.get("superseded_by") is not None and v.get("is_canonical") is True:
            errs.append("superseded version may not be canonical")

    return errs


def validate_supersession_bidirectional(versions: List[Dict[str, Any]]) -> List[str]:
    errs: List[str] = []
    by_id: Dict[str, Dict[str, Any]] = {}
    for v in versions:
        vid = v.get("version_id")
        if isinstance(vid, str):
            by_id[vid] = v

    for v in versions:
        vid = v.get("version_id")
        if not isinstance(vid, str):
            continue

        supersedes = v.get("supersedes")
        if supersedes is not None:
            if supersedes not in by_id:
                errs.append(f"supersedes points to missing version_id: {supersedes}")
            else:
                back = by_id[supersedes].get("superseded_by")
                if back != vid:
                    errs.append(
                        f"bidirectional supersession mismatch: {vid}.supersedes={supersedes} "
                        f"but {supersedes}.superseded_by={back}"
                    )

        superseded_by = v.get("superseded_by")
        if superseded_by is not None:
            if superseded_by not in by_id:
                errs.append(f"superseded_by points to missing version_id: {superseded_by}")
            else:
                back = by_id[superseded_by].get("supersedes")
                if back != vid:
                    errs.append(
                        f"bidirectional supersession mismatch: {vid}.superseded_by={superseded_by} "
                        f"but {superseded_by}.supersedes={back}"
                    )
    return errs


def order_versions_deterministically(versions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(v: Dict[str, Any]):
        vn = v.get("version_number")
        if not isinstance(vn, int):
            vn = 0
        dt = _parse_iso8601_utc(v.get("created_at", "")) or datetime(1970, 1, 1, tzinfo=timezone.utc)
        vid = v.get("version_id")
        if not isinstance(vid, str):
            vid = ""
        return (vn, dt, vid)

    return sorted(list(versions), key=key)


def get_prev_next_version_ids(ordered_versions: List[Dict[str, Any]], current_version_id: str):
    if not isinstance(current_version_id, str) or not current_version_id:
        return (None, None)

    ids = [v.get("version_id") for v in ordered_versions]
    try:
        idx = ids.index(current_version_id)
    except ValueError:
        return (None, None)

    prev_id = ordered_versions[idx - 1].get("version_id") if idx - 1 >= 0 else None
    next_id = ordered_versions[idx + 1].get("version_id") if idx + 1 < len(ordered_versions) else None

    if not isinstance(prev_id, str):
        prev_id = None
    if not isinstance(next_id, str):
        next_id = None
    return (prev_id, next_id)


def build_presentation_index_v1(versions: List[Dict[str, Any]]) -> PresentationIndexV1:
    schema_errs = validate_version_set_schema(versions)
    if schema_errs:
        return PresentationIndexV1(
            versions=[],
            canonical_version_id=None,
            status=PresentationStatus.error,
            integrity_violations=[],
            error="; ".join(schema_errs),
        )

    ordered = order_versions_deterministically(versions)

    canonical_errs = validate_canonical_constraints(ordered)
    if canonical_errs:
        return PresentationIndexV1(
            versions=ordered,
            canonical_version_id=None,
            status=PresentationStatus.withheld,
            integrity_violations=[],
            error="; ".join(canonical_errs),
        )

    integrity = validate_supersession_bidirectional(ordered)
    canonical = [v for v in ordered if v.get("is_canonical") is True]
    canonical_id = canonical[0].get("version_id") if canonical else None
    if not isinstance(canonical_id, str):
        canonical_id = None

    return PresentationIndexV1(
        versions=ordered,
        canonical_version_id=canonical_id,
        status=PresentationStatus.ok,
        integrity_violations=integrity,
        error=None,
    )
