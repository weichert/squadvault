from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "selection_set_schema_v1.py"

MARKER = "__all__ = ["

HELPERS_BLOCK = r'''
# ----------------------------
# Deterministic sort helpers (v1.0)
# ----------------------------

def deterministic_sort_str(values: list[str]) -> list[str]:
    return sorted(values)

def deterministic_sort_excluded(values: list["ExcludedSignal"]) -> list["ExcludedSignal"]:
    return sorted(values, key=lambda x: (x.signal_id, x.reason_code.value))

def deterministic_sort_reason_kv(values: list["ReasonDetailKV"]) -> list["ReasonDetailKV"]:
    return sorted(values, key=lambda x: (x.k, x.v))
'''

def _inject_exports(s: str, names: list[str]) -> str:
    # Insert into __all__ right after opening bracket.
    m = re.search(r"__all__\s*=\s*\[\s*\n", s)
    if not m:
        raise SystemExit("ERROR: __all__ list not found or unexpected formatting.")

    insertion = "".join([f'    "{n}",\n' for n in names])
    idx = m.end()
    return s[:idx] + insertion + s[idx:]

def main() -> int:
    s = TARGET.read_text(encoding="utf-8")

    if "def deterministic_sort_str" in s:
        print("OK: deterministic_sort_str already present; nothing to patch.")
        return 0

    if MARKER not in s:
        raise SystemExit(f"ERROR: marker '{MARKER}' not found; refusing to patch.")

    # Insert helpers immediately before __all__
    pre, post = s.split(MARKER, 1)
    s2 = pre.rstrip() + "\n" + HELPERS_BLOCK + "\n\n" + MARKER + post

    # Export the helper names
    s2 = _inject_exports(
        s2,
        ["deterministic_sort_str", "deterministic_sort_excluded", "deterministic_sort_reason_kv"],
    )

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: added deterministic helpers + exports to {TARGET.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
