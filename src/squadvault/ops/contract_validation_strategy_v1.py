from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


class ContractValidationError(ValueError):
    """Fail-closed error for Contract Validation Strategy v1.0."""


class InvariantType(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class Outcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NON_BINDING = "NON_BINDING"  # invariant exists but has no validation coverage
    BLOCKED = "BLOCKED"          # failure blocks progress/release (per semantics)
    WAIVED = "WAIVED"            # explicitly waived (Type B only, with required fields)


@dataclass(frozen=True)
class InvariantSpec:
    invariant_id: str
    invariant_type: Optional[str]  # allow None/unknown to test "default to Type A"
    has_validation: bool


@dataclass(frozen=True)
class WaiverRecord:
    invariant_id: str
    justification: str
    timestamp_utc: str  # ISO-8601 UTC timestamp (string-level; parsed elsewhere if needed)


@dataclass(frozen=True)
class ValidationResult:
    contract_name: str
    contract_version: str
    invariant_id: str
    invariant_type: InvariantType
    outcome: Outcome
    message: str = ""


def _require_nonempty(label: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{label} is required")


def normalize_invariant_type(maybe: Optional[str]) -> InvariantType:
    """
    CVS-A2: Ambiguous/missing classification defaults to Type A (blocking).
    CVS-A1: Closed enum (A/B/C only).
    """
    if maybe is None:
        return InvariantType.A
    s = str(maybe).strip().upper()
    if s in ("A", "TYPE A", "TYPE_A"):
        return InvariantType.A
    if s in ("B", "TYPE B", "TYPE_B"):
        return InvariantType.B
    if s in ("C", "TYPE C", "TYPE_C"):
        return InvariantType.C
    # Unknown -> default A (conservative)
    return InvariantType.A


def decide_outcome(
    *,
    invariant: InvariantSpec,
    contract_name: str,
    contract_version: str,
    validation_passed: Optional[bool],
    waiver: Optional[WaiverRecord] = None,
) -> ValidationResult:
    """
    Core semantics from Contract Validation Strategy v1.0:

    - CVS-A8: results must reference contract name/version/invariant id
    - CVS-A9: never return None; either return ValidationResult or raise (fail-closed)
    - CVS-A3: if no validation coverage => NON_BINDING + dependent work must not proceed
    - CVS-A4: Type A failure => BLOCKED
    - CVS-A5: Type B failure => BLOCKED unless waived with required fields
    - Type C failures => FAIL (logged), not blocking
    - CVS-A6: infra/input failure => raise (fail-closed)
    """
    _require_nonempty("contract_name", contract_name)
    _require_nonempty("contract_version", contract_version)
    _require_nonempty("invariant_id", invariant.invariant_id)

    inv_type = normalize_invariant_type(invariant.invariant_type)

    if not invariant.has_validation:
        return ValidationResult(
            contract_name=contract_name,
            contract_version=contract_version,
            invariant_id=invariant.invariant_id,
            invariant_type=inv_type,
            outcome=Outcome.NON_BINDING,
            message="Missing validation coverage; invariant is non-binding by default",
        )

    if validation_passed is None:
        # Fail closed: infrastructure failure / suppressed validation
        raise ContractValidationError("validation_passed must be explicitly True/False when has_validation=True")

    if validation_passed is True:
        return ValidationResult(
            contract_name=contract_name,
            contract_version=contract_version,
            invariant_id=invariant.invariant_id,
            invariant_type=inv_type,
            outcome=Outcome.PASS,
        )

    # validation_passed is False
    if inv_type == InvariantType.A:
        return ValidationResult(
            contract_name=contract_name,
            contract_version=contract_version,
            invariant_id=invariant.invariant_id,
            invariant_type=inv_type,
            outcome=Outcome.BLOCKED,
            message="Type A failure blocks progress",
        )

    if inv_type == InvariantType.B:
        if waiver is None:
            return ValidationResult(
                contract_name=contract_name,
                contract_version=contract_version,
                invariant_id=invariant.invariant_id,
                invariant_type=inv_type,
                outcome=Outcome.BLOCKED,
                message="Type B failure blocks by default; waiver required",
            )
        # Waiver required fields
        _require_nonempty("waiver.justification", waiver.justification)
        _require_nonempty("waiver.timestamp_utc", waiver.timestamp_utc)
        return ValidationResult(
            contract_name=contract_name,
            contract_version=contract_version,
            invariant_id=invariant.invariant_id,
            invariant_type=inv_type,
            outcome=Outcome.WAIVED,
            message="Type B failure waived explicitly",
        )

    # Type C
    return ValidationResult(
        contract_name=contract_name,
        contract_version=contract_version,
        invariant_id=invariant.invariant_id,
        invariant_type=inv_type,
        outcome=Outcome.FAIL,
        message="Type C failure is non-blocking (log/review)",
    )


def most_conservative(outcomes: Sequence[Outcome]) -> Outcome:
    """
    CVS-A7: Most conservative outcome applies.

    Deterministic ordering (most conservative first):
    BLOCKED > NON_BINDING > FAIL > WAIVED > PASS
    """
    if outcomes is None:
        raise ContractValidationError("outcomes is required")
    rank = {
        Outcome.BLOCKED: 0,
        Outcome.NON_BINDING: 1,
        Outcome.FAIL: 2,
        Outcome.WAIVED: 3,
        Outcome.PASS: 4,
    }
    best = None
    for o in outcomes:
        if not isinstance(o, Outcome):
            raise ContractValidationError(f"Unknown outcome: {o!r}")
        if best is None or rank[o] < rank[best]:
            best = o
    if best is None:
        raise ContractValidationError("outcomes must not be empty")
    return best
