import pytest

from squadvault.ops.approval_authority_v1 import (
    ApprovalAuthorityError,
    BulkApprovalRequest,
    MAX_BULK_ARTIFACTS,
    validate_bulk_approval_request,
)


def test_bulk_allows_primary_approved_under_limit():
    req = BulkApprovalRequest(actor_role="primary", artifact_ids=["a1", "a2", "a3"], action="approved")
    validate_bulk_approval_request(req)


def test_bulk_allows_co_commissioner_approved_under_limit():
    req = BulkApprovalRequest(actor_role="co_commissioner", artifact_ids=["a1"], action="approved")
    validate_bulk_approval_request(req)


def test_bulk_rejects_unknown_role_default_deny():
    req = BulkApprovalRequest(actor_role="ai_system", artifact_ids=["a1"], action="approved")
    with pytest.raises(ApprovalAuthorityError, match="Forbidden actor_role"):
        validate_bulk_approval_request(req)


def test_bulk_rejects_delegate_bulk_ops():
    req = BulkApprovalRequest(actor_role="delegate", artifact_ids=["a1"], action="approved")
    with pytest.raises(ApprovalAuthorityError, match="Delegated approvers may not perform bulk operations"):
        validate_bulk_approval_request(req)


def test_bulk_enforces_max_20():
    req = BulkApprovalRequest(
        actor_role="primary",
        artifact_ids=[f"a{i}" for i in range(MAX_BULK_ARTIFACTS + 1)],
        action="approved",
    )
    with pytest.raises(ApprovalAuthorityError, match="exceeds max"):
        validate_bulk_approval_request(req)


def test_bulk_forbids_bulk_withheld():
    req = BulkApprovalRequest(actor_role="primary", artifact_ids=["a1", "a2"], action="withheld")
    with pytest.raises(ApprovalAuthorityError, match="Bulk rejection/withholding is forbidden"):
        validate_bulk_approval_request(req)


def test_bulk_default_deny_unknown_action():
    req = BulkApprovalRequest(actor_role="primary", artifact_ids=["a1"], action="auto_approve")
    with pytest.raises(ApprovalAuthorityError, match="Forbidden action"):
        validate_bulk_approval_request(req)


def test_bulk_rejects_empty_artifact_ids():
    req = BulkApprovalRequest(actor_role="primary", artifact_ids=[], action="approved")
    with pytest.raises(ApprovalAuthorityError, match="must not be empty"):
        validate_bulk_approval_request(req)
