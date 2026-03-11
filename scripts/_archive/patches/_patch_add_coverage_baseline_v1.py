from __future__ import annotations

from pathlib import Path
import ast

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "src" / "pfl" / "coverage_baseline_v1.py"

def _needs_tuple_literal(enum_name: str, needs: tuple[object, ...]) -> str:
    # Deterministic, no sorting: preserve order of `needs`.
    # Emit valid Python: (InputNeed.A, InputNeed.B, ...)
    parts: list[str] = []
    for n in needs:
        name = getattr(n, "name", None)
        if not isinstance(name, str) or not name:
            raise RuntimeError(f"Expected enum member with .name, got {n!r}")
        parts.append(f"{enum_name}.{name}")
    if len(parts) == 1:
        return f"({parts[0]},)"
    return "(" + ", ".join(parts) + ")"

def main() -> None:
    from pfl.registry import STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1
    from pfl.planning import resolve_show_plan
    from pfl.coverage import resolve_input_need_coverage

    plan = resolve_show_plan(STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1)
    cov = resolve_input_need_coverage(plan)
    needs = cov.needs

    if not isinstance(needs, tuple):
        raise RuntimeError(f"Expected coverage.needs tuple, got {type(needs)}")
    if len(needs) == 0:
        raise RuntimeError("coverage.needs unexpectedly empty; refusing to snapshot baseline")
    if len(needs) != len(set(needs)):
        raise RuntimeError("Baseline generation found duplicates in coverage.needs (unexpected)")

    input_need_type = type(needs[0])
    input_need_mod = input_need_type.__module__
    input_need_name = input_need_type.__name__
    if input_need_name != "InputNeed":
        raise RuntimeError(f"Expected InputNeed enum, got {input_need_type}")

    needs_literal = _needs_tuple_literal(input_need_name, needs)

    content = f'''"""
Frozen baseline snapshot: STANDARD_SHOW_V1 InputNeed coverage (v1)

HARD RULES:
- Constant only (no dynamic computation)
- Tuple only
- No registry import
- No resolve_show_plan call
- No duplicates
"""

from __future__ import annotations

from {input_need_mod} import {input_need_name}

# Frozen contract surface: exact tuple snapshot (stable deterministic order).
STANDARD_SHOW_V1_INPUT_NEEDS_BASELINE: tuple[InputNeed, ...] = {needs_literal}
'''
    ast.parse(content)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"OK: wrote baseline snapshot -> {OUT}")
    print(f"    count={len(needs)}")

if __name__ == "__main__":
    main()
