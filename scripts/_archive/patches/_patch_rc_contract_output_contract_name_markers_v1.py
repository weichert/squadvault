from __future__ import annotations

from pathlib import Path

DOC = "docs/contracts/rivalry_chronicle_contract_output_v1.md"
NAME = "RIVALRY_CHRONICLE_CONTRACT_OUTPUT_V1"

TARGETS = [
    Path("scripts/gate_rivalry_chronicle_output_contract_v1.sh"),
    Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh"),
]

NAME_LINE = f"# SV_CONTRACT_NAME: {NAME}"
DOC_LINE = f"# SV_CONTRACT_DOC_PATH: {DOC}"

def norm(s: str) -> str:
    return s.replace("\r\n", "\n")

def patch_file(p: Path) -> bool:
    s0 = norm(p.read_text(encoding="utf-8"))
    lines = s0.splitlines(True)

    changed = False

    # Replace any existing SV_CONTRACT_NAME line, else insert.
    found_name = False
    for i, ln in enumerate(lines):
        if ln.rstrip("\n").startswith("# SV_CONTRACT_NAME:"):
            if ln.rstrip("\n") != NAME_LINE:
                lines[i] = NAME_LINE + "\n"
                changed = True
            found_name = True
            break

    # Replace any existing SV_CONTRACT_DOC_PATH line, else insert.
    found_doc = False
    for i, ln in enumerate(lines):
        if ln.rstrip("\n").startswith("# SV_CONTRACT_DOC_PATH:"):
            if ln.rstrip("\n") != DOC_LINE:
                lines[i] = DOC_LINE + "\n"
                changed = True
            found_doc = True
            break

    # If missing, insert markers near the top (after shebang if present).
    if not found_name or not found_doc:
        insert_at = 1 if (lines and lines[0].startswith("#!")) else 0
        block: list[str] = []
        if not found_name:
            block.append(NAME_LINE + "\n")
        if not found_doc:
            block.append(DOC_LINE + "\n")
        # Keep a blank line after markers if not already there.
        block.append("\n")
        lines[insert_at:insert_at] = block
        changed = True

    s1 = "".join(lines)
    if changed:
        p.write_text(s1, encoding="utf-8")
    return changed

def main() -> None:
    any_changed = 0
    for p in TARGETS:
        if not p.exists():
            raise SystemExit(f"ERROR: expected {p} to exist")
        if patch_file(p):
            any_changed += 1
    print(f"OK: patched {any_changed} file(s)")

if __name__ == "__main__":
    main()
