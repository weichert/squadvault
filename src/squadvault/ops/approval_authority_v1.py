from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


class ApprovalAuthorityError(ValueError):
    """Fail-closed validation error for Approval Authority contract invariants."""


ActorRole = Literal["primary", "co_commissioner", "delegate"]
ApprovalAction = Literal["approved", "withheld", "regenerate_requested", "annotated"]

MAX_BULK_ARTIFACTS = 20


@dataclass(frozen=True)
class BulkApprovalRequest:
    actor_role: str
    artifact_ids: Sequence[str]
    action: str  # validate to ApprovalAction; keep as str to fail-closed on unknowns


def validate_actor_role(role: str) -> ActorRole:
    if role in ("primary", "co_commissioner", "delegate"):
        return role  # type: ignore[return-value]
    raise ApprovalAuthorityError(f"Forbidden actor_role (default deny): {role!r}")


def validate_bulk_approval_request(req: BulkApprovalRequest) -> None:
    """
    Type A invariants from Approval Authority v1.0 (unit-testable):

    - Default deny on unknown roles/actions
    - Closed enum roles: primary | co_commissioner | delegate
    - Delegated approvers may not perform bulk operations
    - Bulk operations max 20 artifacts
    - Bulk rejection/withholding is forbidden (must be explicit per artifact)
    """
    role = validate_actor_role(req.actor_role)

    if not isinstance(req.artifact_ids, (list, tuple)):
        raise ApprovalAuthorityError("artifact_ids must be a list/tuple of artifact ids")

    if len(req.artifact_ids) == 0:
        raise ApprovalAuthorityError("artifact_ids must not be empty")

    if len(req.artifact_ids) > MAX_BULK_ARTIFACTS:
        raise ApprovalAuthorityError(
            f"Bulk approval exceeds max {MAX_BULK_ARTIFACTS}: got {len(req.artifact_ids)}"
        )

    if role == "delegate":
        raise ApprovalAuthorityError("Delegated approvers may not perform bulk operations")

    if req.action not in ("approved", "withheld", "regenerate_requested", "annotated"):
        raise ApprovalAuthorityError(f"Forbidden action (default deny): {req.action!r}")

    if req.action == "withheld":
        raise ApprovalAuthorityError(
            "Bulk rejection/withholding is forbidden; must be explicit per artifact"
        )
