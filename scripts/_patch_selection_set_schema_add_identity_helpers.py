from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "selection_set_schema_v1.py"

INSERT_MARKER = "__all__ = ["

HELPERS_BLOCK = r'''
# ----------------------------
# Identity helpers (v1.0)
# ----------------------------
# NOTE: These are deterministic helpers used by tests and higher-level callers.
# They do not change schema; they provide canonical hashing recipes.

from hashlib import sha256

def _sha256_hex(s: str) -> str:
    return sha256(s.encode("utf-8")).hexdigest()

def build_selection_fingerprint(
    *,
    league_id: str,
    season: int,
    week_index: int,
    window_id: str,
    included_signal_ids: list[str],
    excluded: list["ExcludedSignal"],
) -> str:
    """
    Deterministic fingerprint recipe:
    - Stable concatenation of core identity + sorted ids + (signal_id, reason_code) pairs
    - SHA256 hex digest
    """
    inc = ",".join(sorted(included_signal_ids))
    exc = ",".join(
        f"{e.signal_id}:{e.reason_code.value}"
        for e in sorted(excluded, key=lambda x: (x.signal_id, x.reason_code.value))
    )
    payload = f"{league_id}|{season}|{week_index}|{window_id}|{inc}|{exc}"
    return _sha256_hex(payload)

def build_selection_set_id(selection_fingerprint: str) -> str:
    # Simple deterministic id: sha256 of fingerprint
    return _sha256_hex(selection_fingerprint)

def build_group_id(*, group_basis: "GroupBasisCode", signal_ids: list[str]) -> str:
    payload = group_basis.value + "|" + "|".join(sorted(signal_ids))
    return _sha256_hex(payload)
'''

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if "def build_selection_fingerprint" in s:
        print("OK: identity helpers already present; nothing to patch.")
        return 0

    if INSERT_MARKER not in s:
        raise SystemExit(f"ERROR: cannot find marker '{INSERT_MARKER}' in schema; refusing to patch.")

    # Insert helpers right before __all__ block
    parts = s.split(INSERT_MARKER, 1)
    s2 = parts[0].rstrip() + "\n" + HELPERS_BLOCK + "\n\n" + INSERT_MARKER + parts[1]

    # Also add exports to __all__
    # (Conservative: only if __all__ exists and is list literal.)
    # We’ll inject three names near the top of the __all__ list.
    s2b = s2
    m = re.search(r"__all__\s*=\s*\[\s*", s2b)
    if not m:
        raise SystemExit("ERROR: __all__ format unexpected; refusing to patch exports.")

    insert_exports = (
        '    "build_selection_fingerprint",\n'
        '    "build_selection_set_id",\n'
        '    "build_group_id",\n'
    )
    # Insert right after opening bracket
    idx = m.end()
    s2b = s2b[:idx] + insert_exports + s2b[idx:]

    TARGET.write_text(s2b, encoding="utf-8")
    print(f"OK: added identity helpers + exports to {TARGET.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
