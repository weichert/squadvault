#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_if_changed(p: Path, s0: str, s1: str) -> bool:
    if s1 != s0:
        p.write_text(s1, encoding="utf-8")
        return True
    return False

def replace_exact_once(p: Path, s: str, needle: str, repl: str, label: str) -> str:
    n = s.count(needle)
    if n == 0:
        # idempotent: treat as already patched only if the replacement is present
        if repl in s:
            return s
        die(f"{p}: '{label}' expected to find exact needle, found 0")
    if n != 1:
        die(f"{p}: '{label}' expected 1 occurrence, found {n}")
    return s.replace(needle, repl, 1)

def ensure_anchor_present(p: Path, s: str, pattern: str, label: str) -> None:
    if not re.search(pattern, s, flags=re.MULTILINE):
        die(f"{p}: missing required anchor for '{label}'")

def patch_scripts_recap() -> bool:
    p = REPO_ROOT / "scripts" / "recap"
    if not p.exists():
        die("scripts/recap not found")

    s0 = read(p)
    s = s0

    ensure_anchor_present(p, s, r"^#\s*Delegates to scripts/recap\.py", "recap shim header")

    needle = 'PYTHONPATH=src exec python -u scripts/recap.py "$@"\n'
    repl = (
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"\n'
        '\n'
        '# Delegate to the canonical shim (CWD-independent, shim-first).\n'
        'exec "${SCRIPT_DIR}/recap.sh" "$@"\n'
    )

    s = replace_exact_once(p, s, needle, repl, "remove PYTHONPATH shim line")

    return write_if_changed(p, s0, s)

def patch_writing_room_select() -> bool:
    p = REPO_ROOT / "scripts" / "writing_room_select_v1.sh"
    if not p.exists():
        die("scripts/writing_room_select_v1.sh not found")

    s0 = read(p)
    s = s0

    ensure_anchor_present(p, s, r"^\s*ROOT=", "ROOT var")

    s = replace_exact_once(
        p,
        s,
        'exec "$ROOT/scripts/recap.py" check \\\n',
        'exec "$ROOT/scripts/recap.sh" check \\\n',
        "recap.py -> recap.sh (writing room select)",
    )

    return write_if_changed(p, s0, s)

def patch_prove_golden_path() -> bool:
    p = REPO_ROOT / "scripts" / "prove_golden_path.sh"
    if not p.exists():
        die("scripts/prove_golden_path.sh not found")

    s0 = read(p)
    s = s0

    ensure_anchor_present(p, s, r"^\s*REPO_ROOT=", "REPO_ROOT var")

    s = replace_exact_once(
        p,
        s,
        'python3 Tests/_nac_check_assembly_plain_v1.py "$ASSEMBLY"\n',
        '"$REPO_ROOT/scripts/py" "$REPO_ROOT/Tests/_nac_check_assembly_plain_v1.py" "$ASSEMBLY"\n',
        "python3 + relative Tests path -> scripts/py + absolute",
    )

    return write_if_changed(p, s0, s)

def main() -> int:
    changed = False
    changed |= patch_scripts_recap()
    changed |= patch_writing_room_select()
    changed |= patch_prove_golden_path()

    print("OK: ops shim + CWD-independence polish applied." if changed else "OK: no changes needed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
