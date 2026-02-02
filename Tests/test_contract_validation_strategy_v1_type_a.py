import pytest

from squadvault.ops.contract_validation_strategy_v1 import (
    ContractValidationError,
    InvariantSpec,
    InvariantType,
    Outcome,
    WaiverRecord,
    decide_outcome,
    most_conservative,
    normalize_invariant_type,
)


CONTRACT_NAME = "Contract Validation Strategy"
CONTRACT_VERSION = "v1.0"


def test_normalize_invariant_type_closed_enum_and_default_to_a():
    assert normalize_invariant_type("A") == InvariantType.A
    assert normalize_invariant_type("B") == InvariantType.B
    assert normalize_invariant_type("C") == InvariantType.C
    assert normalize_invariant_type(None) == InvariantType.A
    assert normalize_invariant_type("nonsense") == InvariantType.A  # default-to-A conservative


def test_missing_validation_renders_non_binding():
    inv = InvariantSpec(invariant_id="CVS-X1", invariant_type="B", has_validation=False)
    r = decide_outcome(
        invariant=inv,
        contract_name=CONTRACT_NAME,
        contract_version=CONTRACT_VERSION,
        validation_passed=None,  # irrelevant when has_validation=False
        waiver=None,
    )
    assert r.outcome == Outcome.NON_BINDING


def test_has_validation_requires_explicit_true_false_fail_closed():
    inv = InvariantSpec(invariant_id="CVS-X2", invariant_type="A", has_validation=True)
    with pytest.raises(ContractValidationError, match="validation_passed must be explicitly"):
        decide_outcome(
            invariant=inv,
            contract_name=CONTRACT_NAME,
            contract_version=CONTRACT_VERSION,
            validation_passed=None,
            waiver=None,
        )


def test_type_a_failure_blocks():
    inv = InvariantSpec(invariant_id="CVS-A1", invariant_type="A", has_validation=True)
    r = decide_outcome(
        invariant=inv,
        contract_name=CONTRACT_NAME,
        contract_version=CONTRACT_VERSION,
        validation_passed=False,
        waiver=None,
    )
    assert r.outcome == Outcome.BLOCKED


def test_type_b_failure_blocks_without_waiver():
    inv = InvariantSpec(invariant_id="CVS-B1", invariant_type="B", has_validation=True)
    r = decide_outcome(
        invariant=inv,
        contract_name=CONTRACT_NAME,
        contract_version=CONTRACT_VERSION,
        validation_passed=False,
        waiver=None,
    )
    assert r.outcome == Outcome.BLOCKED


def test_type_b_failure_waived_requires_fields():
    inv = InvariantSpec(invariant_id="CVS-B2", invariant_type="B", has_validation=True)

    with pytest.raises(ContractValidationError, match="waiver.justification is required"):
        decide_outcome(
            invariant=inv,
            contract_name=CONTRACT_NAME,
            contract_version=CONTRACT_VERSION,
            validation_passed=False,
            waiver=WaiverRecord(invariant_id="CVS-B2", justification="", timestamp_utc="2026-01-28T00:00:00Z"),
        )

    r = decide_outcome(
        invariant=inv,
        contract_name=CONTRACT_NAME,
        contract_version=CONTRACT_VERSION,
        validation_passed=False,
        waiver=WaiverRecord(invariant_id="CVS-B2", justification="release gate waived for test", timestamp_utc="2026-01-28T00:00:00Z"),
    )
    assert r.outcome == Outcome.WAIVED


def test_type_c_failure_non_blocking_fail():
    inv = InvariantSpec(invariant_id="CVS-C1", invariant_type="C", has_validation=True)
    r = decide_outcome(
        invariant=inv,
        contract_name=CONTRACT_NAME,
        contract_version=CONTRACT_VERSION,
        validation_passed=False,
        waiver=None,
    )
    assert r.outcome == Outcome.FAIL


def test_results_require_contract_name_version_and_invariant_id_fail_closed():
    inv = InvariantSpec(invariant_id="  ", invariant_type="A", has_validation=False)
    with pytest.raises(ContractValidationError, match="invariant_id is required"):
        decide_outcome(
            invariant=inv,
            contract_name=CONTRACT_NAME,
            contract_version=CONTRACT_VERSION,
            validation_passed=None,
            waiver=None,
        )


def test_most_conservative_ordering_deterministic():
    assert most_conservative([Outcome.PASS, Outcome.WAIVED]) == Outcome.WAIVED
    assert most_conservative([Outcome.PASS, Outcome.FAIL]) == Outcome.FAIL
    assert most_conservative([Outcome.FAIL, Outcome.NON_BINDING]) == Outcome.NON_BINDING
    assert most_conservative([Outcome.NON_BINDING, Outcome.BLOCKED]) == Outcome.BLOCKED
