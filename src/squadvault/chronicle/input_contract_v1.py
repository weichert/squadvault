from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, Tuple


class MissingWeeksPolicy(str, Enum):
    REFUSE = "refuse"
    ACKNOWLEDGE_MISSING = "acknowledge_missing"


@dataclass(frozen=True)
class ApprovedRecapRefV1:
    """
    Minimal pointer to an APPROVED weekly recap artifact.
    Sufficient to fetch the approved artifact body later.
    """
    week_index: int
    artifact_type: str
    version: int
    selection_fingerprint: str


@dataclass(frozen=True)
class RivalryChronicleInputV1:
    league_id: int
    season: int

    # Exactly one of these must be provided:
    week_indices: Optional[Tuple[int, ...]] = None
    week_range: Optional[Tuple[int, int]] = None  # inclusive

    missing_weeks_policy: MissingWeeksPolicy = MissingWeeksPolicy.REFUSE

    # Optional explicit refs (still validated). If None, resolver loads from DB.
    approved_recaps: Optional[Tuple[ApprovedRecapRefV1, ...]] = None

    def normalized_week_indices(self) -> Tuple[int, ...]:
        if (self.week_indices is None) == (self.week_range is None):
            raise ValueError("Provide exactly one of: week_indices OR week_range")

        if self.week_indices is not None:
            weeks = list(self.week_indices)
        else:
            start, end = self.week_range  # type: ignore[misc]
            if int(start) > int(end):
                raise ValueError("week_range start must be <= end")
            weeks = list(range(int(start), int(end) + 1))

        weeks = sorted(set(int(w) for w in weeks))
        if not weeks:
            raise ValueError("At least one week must be specified")
        if any(w < 0 for w in weeks):
            raise ValueError("week indices must be >= 0")
        return tuple(weeks)


@dataclass(frozen=True)
class ResolvedChronicleInputV1:
    league_id: int
    season: int
    week_indices: Tuple[int, ...]
    missing_weeks_policy: MissingWeeksPolicy
    approved_recaps: Tuple[ApprovedRecapRefV1, ...]

    @property
    def missing_weeks(self) -> Tuple[int, ...]:
        present = {r.week_index for r in self.approved_recaps}
        missing = [w for w in self.week_indices if w not in present]
        return tuple(missing)


class ChronicleInputResolverV1:
    """
    Boundary enforcer:
    - resolves requested weeks into APPROVED recap refs
    - enforces missing weeks policy
    """

    def __init__(self, approved_recap_loader):
        """
        approved_recap_loader signature:
          (league_id:int, season:int, week_indices:Sequence[int]) -> Sequence[ApprovedRecapRefV1]
        """
        self._load_approved = approved_recap_loader

    def resolve(self, inp: RivalryChronicleInputV1) -> ResolvedChronicleInputV1:
        weeks = inp.normalized_week_indices()

        if inp.approved_recaps is not None:
            recaps = tuple(sorted(inp.approved_recaps, key=lambda r: r.week_index))
        else:
            loaded = self._load_approved(int(inp.league_id), int(inp.season), weeks)
            recaps = tuple(sorted(loaded, key=lambda r: r.week_index))

        resolved = ResolvedChronicleInputV1(
            league_id=int(inp.league_id),
            season=int(inp.season),
            week_indices=weeks,
            missing_weeks_policy=inp.missing_weeks_policy,
            approved_recaps=recaps,
        )

        missing = resolved.missing_weeks
        if missing and resolved.missing_weeks_policy == MissingWeeksPolicy.REFUSE:
            raise ValueError(f"Missing APPROVED recaps for weeks: {list(missing)}")

        # Guardrail: approved_recaps must not include weeks outside request.
        req = set(resolved.week_indices)
        extra = [r.week_index for r in resolved.approved_recaps if r.week_index not in req]
        if extra:
            raise ValueError(f"Approved recap refs include weeks not requested: {extra}")

        return resolved
