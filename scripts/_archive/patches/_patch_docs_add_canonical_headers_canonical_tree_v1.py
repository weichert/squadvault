from __future__ import annotations

import re
from pathlib import Path

CHECKER = Path("scripts/check_docs_integrity_v1.py")

# Only touch the failing canonical tree files (explicit allowlist).
TARGETS = [
    Path("docs/canonical/Core_Invariants_Registry_v1.0.md"),
    Path("docs/canonical/Golden_Path_Production_Freeze_v1.0.md"),
    Path("docs/canonical/contracts/Approval_Authority_Contract_Card_v1.0.md"),
    Path("docs/canonical/contracts/EAL_Calibration_Contract_v1.0.md"),
    Path("docs/canonical/contracts/Tone_Engine_Contract_Card_v1.0.md"),
    Path("docs/canonical/contracts/ops/Ops_Shim_and_CWD_Independence_Contract_v1.0.md"),
    Path("docs/canonical/contracts/signals/Signal_Taxonomy_Contract_v1.0.md"),
    Path("docs/canonical/specs/signals/Signal_Catalog_v1.0.md"),
]

MARK = "docs_add_canonical_headers_canonical_tree_v1"

def die(msg: str) -> None:
    raise SystemExit(msg)

def read_canon_header_marker() -> str:
    if not CHECKER.exists():
        die(f"FAIL: checker missing: {CHECKER}")

    s = CHECKER.read_text(encoding="utf-8")

    # Prefer the checker’s authoritative constant.
    m = re.search(r'(?m)^CANON_HEADER\s*=\s*["\'](.+?)["\']\s*$', s)
    if m:
        return m.group(1)

    # Fallback (should not happen, but keep deterministic).
    return "[SV_CANONICAL_HEADER_V1]"

def normalize_newlines(s: str) -> str:
    # Keep repo policy consistent
    return s.replace("\r\n", "\n").replace("\r", "\n")

def ensure_header(p: Path, header: str) -> bool:
    if not p.exists():
        die(f"FAIL: missing target file: {p}")

    txt = normalize_newlines(p.read_text(encoding="utf-8", errors="replace"))

    if header in txt:
        return False

    # Prepend marker + blank line.
    out = f"{header}\n\n{txt.lstrip()}"
    p.write_text(out, encoding="utf-8", newline="\n")
    return True

def main() -> None:
    header = read_canon_header_marker()

    changed: list[str] = []
    for p in TARGETS:
        if ensure_header(p, header):
            changed.append(str(p))

    if changed:
        print("OK: inserted canonical header marker into:")
        for c in changed:
            print(f"  - {c}")
    else:
        print("NO-OP: all targets already contain canonical header marker")

if __name__ == "__main__":
    main()
