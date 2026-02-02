from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> int:
    if not P.exists():
        die(f"Missing file: {P}")

    s = P.read_text(encoding="utf-8")

    if "def build_selection_set_v1" not in s:
        die("Missing build_selection_set_v1; refusing.")

    pat = r"(?m)^return SelectionSetV1\(\s*$"
    if not re.search(pat, s):
        die("Did not find a column-0 'return SelectionSetV1(' line to indent. Refusing (state drift).")

    s2, n = re.subn(pat, "    return SelectionSetV1(", s, count=1)
    if n != 1:
        die(f"Expected to patch exactly 1 column-0 return; patched {n}.")

    P.write_text(s2, encoding="utf-8")
    print(f"OK: indented column-0 return SelectionSetV1( in {P.relative_to(ROOT)}")
    print("Next:")
    print("  python -m py_compile src/squadvault/recaps/writing_room/intake_v1.py")
    print("  pytest")
    print("  ./scripts/test.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
