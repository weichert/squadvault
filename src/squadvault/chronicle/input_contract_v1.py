from __future__ import annotations
# SV_PATCH_RC_INPUT_CONTRACT_FIX_RESOLVE_V4: replace resolve() block (brace-escaped)
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_ALL_IMPORT_TIME_BAD_BLOCKS_V1: delete all import-time bad blocks (inp/resolved)
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_ALL_IMPORT_TIME_INP_BLOCKS_V1: delete all import-time inp blocks
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_ORPHAN_INP_BLOCK_V2: delete import-time inp block (outside def/class)
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_STRAY_RETURN_LINE154_V1: delete stray module-scope return
# SV_PATCH_RC_INPUT_CONTRACT_FIX_MISSING_IF_BODY_LINE149_V1: insert pass if if-body missing
# SV_PATCH_RC_INPUT_CONTRACT_FIX_MISSING_IF_BODY_LINE141_V1: insert pass if if-body missing
# SV_PATCH_RC_INPUT_CONTRACT_REPAIR_INDENT_WINDOW_V2: dedent illegal indents in tail window
# SV_PATCH_RC_INPUT_CONTRACT_FIX_INDENT_LINE143_V2: force line 143 indent to valid stack level
# SV_PATCH_RC_INPUT_CONTRACT_EXPANDTABS_V7: expand tabs to spaces to fix mixed-indent errors
# SV_PATCH_RC_INPUT_CONTRACT_SCRUB_TOPLEVEL_INDENT_V6: remove unexpected top-level indentation (paren-aware)
# SV_PATCH_RC_RESOLVED_INPUT_ADD_MISSING_WEEKS_V3: add missing_weeks field + pass it in resolve()
from dataclasses import dataclass
# SV_PATCH_RC_INPUT_CONTRACT_DATACLASS_IMPORT_TOP_V1: ensure dataclass import appears before first @dataclass


# SV_PATCH_RC_DEFINE_RESOLVED_INPUT_V2: define ResolvedChronicleInputV1 inferred from regex-balanced callsite
@dataclass(frozen=True)
class ResolvedChronicleInputV1:
    league_id: Any
    season: Any
    week_indices: Any
    missing_weeks: Any
    missing_weeks_policy: Any
    approved_recaps: Any

from enum import Enum
from typing import Optional, Sequence, Tuple, Any


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

    def normalized_week_indices(self):
        # SV_PATCH_RC_INPUT_CONTRACT_WEEK_EXCLUSIVITY_RESILIENT_V2: normalized_week_indices prefers week_indices; signature-resilient replacement
        wi = getattr(self, 'week_indices', None)
        wr = getattr(self, 'week_range', None)

        # Prefer explicit week_indices if provided.
        if wi is not None:
            try:
                wi_list = list(wi)
            except TypeError:
                wi_list = [wi]
            if len(wi_list) > 0:
                out = []
                for x in wi_list:
                    out.append(int(x))
                # stable, de-duped
                return sorted(set(out))

        # Otherwise, require a valid week_range.
        if wr is None:
            raise ValueError('Provide exactly one of: week_indices OR week_range')

        # Accept week_range as (start,end) or 'start-end'.
        start = end = None
        if isinstance(wr, str):
            txt = wr.strip()
            if not txt:
                raise ValueError('Provide exactly one of: week_indices OR week_range')
            if '-' not in txt:
                raise ValueError('week_range string must look like "start-end"')
            a, b = [p.strip() for p in txt.split('-', 1)]
            start, end = int(a), int(b)
        else:
            try:
                a, b = wr
            except Exception:
                raise ValueError('week_range must be a 2-tuple (start,end)')
            start, end = int(a), int(b)

        if start > end:
            start, end = end, start
        return list(range(start, end + 1))

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
        """Resolve requested weeks into latest APPROVED recap refs and enforce missing-week policy."""
        weeks = inp.normalized_week_indices()
        weeks_t = tuple(int(w) for w in weeks)
    
        # Load approved refs unless explicitly provided.
        if inp.approved_recaps is None:
            loaded = self._load_approved(int(inp.league_id), int(inp.season), weeks_t)
            approved_all = tuple(loaded)
        else:
            approved_all = tuple(inp.approved_recaps)
    
        # Select latest approved recap per requested week (by max version).
        latest_by_week: dict[int, ApprovedRecapRefV1] = {}
        want = set(weeks_t)
        for ref in approved_all:
            w = int(ref.week_index)
            if w not in want:
                continue
            cur = latest_by_week.get(w)
            if cur is None or int(ref.version) > int(cur.version):
                latest_by_week[w] = ref
    
        approved = tuple(latest_by_week[w] for w in weeks_t if w in latest_by_week)
        present = set(latest_by_week.keys())
        missing = tuple(w for w in weeks_t if w not in present)
    
        policy = inp.missing_weeks_policy
        if missing and policy == MissingWeeksPolicy.REFUSE:
            raise ValueError(f"Missing approved weeks: {missing}")
    
        return ResolvedChronicleInputV1(
            league_id=int(inp.league_id),
            season=int(inp.season),
            week_indices=weeks_t,
            missing_weeks=missing,
            missing_weeks_policy=policy,
            approved_recaps=approved,
        )
