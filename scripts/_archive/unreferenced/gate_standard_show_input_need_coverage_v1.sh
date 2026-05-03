#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHONPATH="$repo_root/src" python - <<'PY'
from __future__ import annotations

from pfl.registry import STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1
from pfl.planning import resolve_show_plan
from pfl.coverage import resolve_input_need_coverage
from pfl.coverage_baseline_v1 import STANDARD_SHOW_V1_INPUT_NEEDS_BASELINE as expected

def _diff(expected: tuple[object, ...], actual: tuple[object, ...]) -> tuple[tuple[object, ...], tuple[object, ...]]:
    # Deterministic, no sorting:
    # - missing preserves expected order
    # - unexpected preserves actual order
    actual_set = set(actual)
    missing = tuple(x for x in expected if x not in actual_set)

    expected_set = set(expected)
    unexpected = tuple(x for x in actual if x not in expected_set)
    return missing, unexpected

plan = resolve_show_plan(STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1)
cov = resolve_input_need_coverage(plan)
actual = cov.needs

if not isinstance(actual, tuple):
    raise SystemExit(f"ERROR: expected coverage.needs tuple, got {type(actual)}")

if actual == expected:
    raise SystemExit(0)

missing, unexpected = _diff(expected, actual)
print(f"missing: {missing!r}")
print(f"unexpected: {unexpected!r}")
print(f"expected: {expected!r}")
print(f"actual: {actual!r}")
raise SystemExit(1)
PY
