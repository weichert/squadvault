from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
import os
import re


class SignalTaxonomyTypeAError(ValueError):
    """Hard-fail error for Type A enforcement when authority is missing/ambiguous."""


@dataclass(frozen=True)
class Rejection:
    signal_id: str
    reason: str


@dataclass(frozen=True)
class TypeAResult:
    accepted: List[Dict[str, Any]]
    rejected: List[Rejection]

    @property
    def accepted_ids(self) -> List[str]:
        return sorted([str(s.get("signal_id", "")) for s in self.accepted])

    @property
    def rejected_ids(self) -> List[str]:
        return sorted([r.signal_id for r in self.rejected])


def _repo_root_from_here() -> Path:
    """
    Resolve repo root deterministically without relying on caller CWD.
    We assume src/squadvault/... lives under <repo>/src/squadvault/...
    """
    here = Path(__file__).resolve()
    parts = list(here.parts)
    if "src" not in parts:
        raise SignalTaxonomyTypeAError(f"Cannot locate repo root (no 'src' in path): {here}")
    idx = parts.index("src")
    return Path(*parts[:idx])


def _find_unique_under(root: Path, filename: str) -> Path:
    matches: List[Path] = []
    for dirpath, _, files in os.walk(root):
        if filename in files:
            matches.append(Path(dirpath) / filename)
    if not matches:
        raise SignalTaxonomyTypeAError(f"Missing canonical authority file under {root}: {filename}")
    if len(matches) > 1:
        raise SignalTaxonomyTypeAError(f"Ambiguous canonical authority (multiple matches) for {filename}: {matches}")
    return matches[0]


_ENUM_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")


def _parse_enum_tokens(md_text: str) -> List[str]:
    """
    Conservative enum parsing:
    - Accept tokens that look like ENUM_CASE.
    - Ignore bracketed placeholder lines like "[Enum lock content ...]".
    """
    tokens: List[str] = []
    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        candidate = line.split("|")[0].strip()
        if _ENUM_TOKEN_RE.match(candidate):
            tokens.append(candidate)
    return sorted(set(tokens))


def _parse_categories_by_type(md_text: str) -> Dict[str, str]:
    """
    Minimal type->category mapping parsing from taxonomy contract markdown.

    Supported patterns:
      1) Headings + bullets:
          ### CATEGORY_NAME
          - TYPE_A
          - TYPE_B

      2) Inline:
          CATEGORY_NAME: TYPE_A

    Any ambiguity (same type in multiple categories) is a hard error.
    """
    type_to_category: Dict[str, str] = {}
    current_category: Optional[str] = None

    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue

        m_heading = re.match(r"^#{2,6}\s+([A-Z][A-Z0-9_]+)\s*$", line)
        if m_heading:
            current_category = m_heading.group(1)
            continue

        m_inline = re.match(r"^([A-Z][A-Z0-9_]+)\s*:\s*([A-Z][A-Z0-9_]+)\s*$", line)
        if m_inline:
            cat, typ = m_inline.group(1), m_inline.group(2)
            prev = type_to_category.get(typ)
            if prev and prev != cat:
                raise SignalTaxonomyTypeAError(
                    f"Taxonomy category ambiguity: type {typ} appears in multiple categories: {prev}, {cat}"
                )
            type_to_category[typ] = cat
            continue

        if current_category:
            bullet = re.sub(r"^[-*]\s+", "", line)
            if _ENUM_TOKEN_RE.match(bullet):
                typ = bullet
                prev = type_to_category.get(typ)
                if prev and prev != current_category:
                    raise SignalTaxonomyTypeAError(
                        f"Taxonomy category ambiguity: type {typ} appears in multiple categories: {prev}, {current_category}"
                    )
                type_to_category[typ] = current_category

    return dict(sorted(type_to_category.items()))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise SignalTaxonomyTypeAError(f"Failed reading canonical file {path}: {e}") from e


class SignalTaxonomyTypeAEnforcerV1:
    """
    Type A enforcement (binding, fail-closed).

    Out of scope: inference, scoring, ranking, persistence, ingestion wiring, Type B.
    """

    def __init__(
        self,
        *,
        signal_taxonomy_contract_path: Optional[Union[str, Path]] = None,
        signal_type_enum_path: Optional[Union[str, Path]] = None,
        tier1_input_contracts_path: Optional[Union[str, Path]] = None,
        tier1_derivation_specs_path: Optional[Union[str, Path]] = None,
    ) -> None:
        repo_root = _repo_root_from_here()
        canon_root = repo_root / "canon"

        self._signal_taxonomy_contract_path = (
            Path(signal_taxonomy_contract_path)
            if signal_taxonomy_contract_path
            else _find_unique_under(canon_root, "Signal_Taxonomy_Contract_v1.0.md")
        )
        self._signal_type_enum_path = (
            Path(signal_type_enum_path)
            if signal_type_enum_path
            else _find_unique_under(canon_root, "Signal_Scout_Signal_Type_Enum_v1.0.md")
        )
        self._tier1_input_contracts_path = (
            Path(tier1_input_contracts_path)
            if tier1_input_contracts_path
            else _find_unique_under(canon_root, "Tier1_Signal_Input_Contracts_v1.0.md")
        )
        self._tier1_derivation_specs_path = (
            Path(tier1_derivation_specs_path)
            if tier1_derivation_specs_path
            else _find_unique_under(canon_root, "Tier1_Signal_Derivation_Specs_v1.0.md")
        )

        self._valid_types = self._load_valid_types()
        self._category_by_type = self._load_category_by_type()

    def _load_valid_types(self) -> List[str]:
        enum_text = _read_text(self._signal_type_enum_path)
        return _parse_enum_tokens(enum_text)  # empty => fail-closed later

    def _load_category_by_type(self) -> Dict[str, str]:
        contract_text = _read_text(self._signal_taxonomy_contract_path)
        mapping = _parse_categories_by_type(contract_text)
        if not mapping:
            raise SignalTaxonomyTypeAError(
                "Signal taxonomy contract provides no type->category mapping; cannot enforce category exclusivity (fail-closed)."
            )
        return mapping

    def enforce(self, signals: Iterable[Dict[str, Any]]) -> TypeAResult:
        accepted: List[Dict[str, Any]] = []
        rejected: List[Rejection] = []

        for s in signals:
            sid = str(s.get("signal_id") or "").strip() or "<missing_signal_id>"
            reason = self._validate_one(s)
            if reason is None:
                accepted.append(s)
            else:
                rejected.append(Rejection(signal_id=sid, reason=reason))

        accepted = sorted(accepted, key=lambda x: str(x.get("signal_id", "")))
        rejected = sorted(rejected, key=lambda r: r.signal_id)
        return TypeAResult(accepted=accepted, rejected=rejected)

    def _validate_one(self, s: Dict[str, Any]) -> Optional[str]:
        # Signal vs Event boundary
        if "event_type" in s or "memory_event_type" in s or "event_id" in s:
            return "EVENT_OBJECT_NOT_A_SIGNAL"

        # Definition enforcement
        sid = s.get("signal_id")
        if not isinstance(sid, str) or not sid.strip():
            return "MISSING_SIGNAL_ID"

        stype = s.get("signal_type")
        if not isinstance(stype, str) or not stype.strip():
            return "MISSING_SIGNAL_TYPE"
        stype = stype.strip()

        # Taxonomy exhaustiveness (empty enum => reject all)
        if not self._valid_types:
            return "SIGNAL_TYPE_ENUM_EMPTY_FAIL_CLOSED"
        if stype not in set(self._valid_types):
            return "UNKNOWN_SIGNAL_TYPE"

        # Exactly-one category
        category_val = s.get("taxonomy_category", s.get("category"))
        categories: List[str] = []
        if isinstance(category_val, str):
            if category_val.strip():
                categories = [category_val.strip()]
        elif isinstance(category_val, list):
            categories = [str(x).strip() for x in category_val if str(x).strip()]

        if len(categories) != 1:
            return "CATEGORY_NOT_EXACTLY_ONE"

        category = categories[0]
        expected_category = self._category_by_type.get(stype)
        if expected_category is None:
            return "TAXONOMY_MISSING_TYPE_CATEGORY"
        if category != expected_category:
            return "CATEGORY_MISMATCH_FOR_TYPE"

        # Derivation lineage required
        derived = s.get("derived_from_event_ids", s.get("derived_from"))
        if isinstance(derived, list):
            derived_ids = [str(x).strip() for x in derived if str(x).strip()]
        elif isinstance(derived, str):
            derived_ids = [derived.strip()] if derived.strip() else []
        else:
            derived_ids = []
        if not derived_ids:
            return "MISSING_DERIVATION_LINEAGE"

        # Truth boundaries
        forbidden_keys = {
            "inferred",
            "inference",
            "causality",
            "cause",
            "motive",
            "intent",
            "strategy",
            "speculation",
            "untracked_enrichment",
            "hidden_enrichment",
        }
        if forbidden_keys.intersection(set(s.keys())):
            return "FORBIDDEN_INFERENCE_FIELDS_PRESENT"

        return None
