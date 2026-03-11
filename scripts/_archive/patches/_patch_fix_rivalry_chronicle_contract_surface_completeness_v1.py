from __future__ import annotations

import subprocess
from pathlib import Path

DOC = Path("docs/contracts/rivalry_chronicle_contract_output_v1.md")
DOC_MARK_LINE = f"# SV_CONTRACT_DOC_PATH: {DOC.as_posix()}"
SECTION_HDR = "## Enforced By"

# Non-enforcement scripts that MUST NOT declare SV_CONTRACT_DOC_PATH per gate_contract_surface_completeness_v1.sh
FORBIDDEN_DECLARERS = [
    Path("scripts/generate_rivalry_chronicle_v1.sh"),
    Path("scripts/persist_rivalry_chronicle_v1.sh"),
    Path("scripts/rivalry_chronicle_generate_v1.sh"),
]

def sh(cmd: str) -> str:
    return subprocess.check_output(["bash", "-lc", cmd], text=True)

def norm(s: str) -> str:
    return s.replace("\r\n", "\n")

def read_text(p: Path) -> str:
    return norm(p.read_text(encoding="utf-8"))

def write_text(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def reverse_scan_enforcement_surfaces() -> list[str]:
    # Mirror gate behavior: grep in scripts/ then filter to scripts/*.sh AND only gate_/prove_ are valid.
    cmd = f"""
set -euo pipefail
MARK={DOC_MARK_LINE!r}
grep -R -n -F -- "$MARK" scripts \
  | cut -d: -f1 \
  | LC_ALL=C sort -u \
  | awk '
      $0 ~ /^scripts\\/gate_.*\\.sh$/ {{print; next}}
      $0 ~ /^scripts\\/prove_.*\\.sh$/ {{print; next}}
    '
"""
    out = sh(cmd).splitlines()
    return [ln.strip() for ln in out if ln.strip()]

def replace_enforced_by_section(doc_txt: str, bullets: list[str]) -> str:
    if SECTION_HDR not in doc_txt:
        raise SystemExit(f"ERROR: missing required section '{SECTION_HDR}' in {DOC}")

    lines = doc_txt.splitlines(True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        out.append(ln)
        if ln.strip() == SECTION_HDR:
            i += 1
            # drop existing body until next '## ' header or EOF
            while i < len(lines) and not lines[i].startswith("## "):
                i += 1
            out.append("\n")
            for p in bullets:
                out.append(f"- `{p}`\n")
            out.append("\n")
            continue
        i += 1
    return "".join(out)

def strip_doc_marker_from_script(path: Path) -> bool:
    if not path.exists():
        return False
    s = read_text(path)
    lines = s.splitlines(True)
    new_lines = [ln for ln in lines if ln.rstrip("\n") != DOC_MARK_LINE]
    new = "".join(new_lines)
    if new != s:
        write_text(path, new)
        return True
    return False

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: expected {DOC} to exist")

    # (A) Remove forbidden declarations in non-enforcement .sh scripts
    removed = 0
    for p in FORBIDDEN_DECLARERS:
        if strip_doc_marker_from_script(p):
            removed += 1
    print(f"OK: removed SV_CONTRACT_DOC_PATH from {removed} non-enforcement script(s)")

    # (B) Compute the authoritative enforcement set (gate/prove only)
    bullets = reverse_scan_enforcement_surfaces()
    if not bullets:
        raise SystemExit(
            "ERROR: no enforcement surfaces found (gate_/prove_). "
            "Expected at least scripts/gate_rivalry_chronicle_output_contract_v1.sh and/or scripts/prove_rivalry_chronicle_end_to_end_v1.sh to declare the doc marker."
        )

    # (C) Rewrite contract Enforced By to EXACTLY that set
    cur = read_text(DOC)
    new = replace_enforced_by_section(cur, bullets).rstrip() + "\n"
    if new == cur.rstrip() + "\n":
        print("OK: contract Enforced By already canonical (idempotent).")
    else:
        write_text(DOC, new)
        print(f"OK: synced Enforced By to {len(bullets)} enforcement surface(s)")

if __name__ == "__main__":
    main()
