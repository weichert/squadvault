from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

ABS_OPEN = "from squadvault.recaps.writing_room.selection_set_schema_v1 import ("
BAD_REL = "from .selection_set_schema_v1 import build_signal_groupings_v1"

# Canonical import block we want to enforce (deterministic)
CANON_BLOCK = """from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    SelectionSetV1,
    ExcludedSignal,
    ReasonDetailKV,
    ExclusionReasonCode,
    WithheldReasonCode,
    build_signal_groupings_v1,
)
"""

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> int:
    if not P.exists():
        die(f"Missing file: {P}")

    s = P.read_text(encoding="utf-8")

    # Fail-fast: only repair when we see the broken pattern
    if ABS_OPEN not in s:
        die(f"Missing expected absolute import opener: {ABS_OPEN!r}")
    if BAD_REL not in s:
        die(f"Missing expected bad inserted line: {BAD_REL!r}")
    if "SelectionSetV1," not in s:
        die("Missing SelectionSetV1 in file; refusing to patch wrong target.")

    # Locate the full absolute import block from opener through the matching closing paren line.
    # We assume the first occurrence is the one to fix.
    m = re.search(
        r"^from squadvault\.recaps\.writing_room\.selection_set_schema_v1 import \(\n([\s\S]*?)^\)\n",
        s,
        flags=re.M,
    )
    if not m:
        die("Could not locate full absolute import block (opener to closing paren). Refusing to guess.")

    full_block = m.group(0)

    # Fail-fast: ensure the bad relative import is inside that block (as observed)
    if BAD_REL not in full_block:
        die("Bad relative import line not found inside the absolute import block; refusing to patch (state drift).")

    s2 = s.replace(full_block, CANON_BLOCK, 1)

    # Sanity checks: exactly one canonical block, and no lingering bad relative import
    if BAD_REL in s2:
        die("Bad relative import still present after replacement; refusing.")
    if s2.count(ABS_OPEN) != 1:
        die(f"Unexpected count of absolute opener after replacement: {s2.count(ABS_OPEN)}")

    if s2 == s:
        print("OK: no changes needed.")
        return 0

    P.write_text(s2, encoding="utf-8")
    print(f"OK: repaired import block in {P.relative_to(ROOT)}")
    print("Next:")
    print("  python -m py_compile src/squadvault/recaps/writing_room/intake_v1.py")
    print("  pytest")
    print("  ./scripts/test.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
