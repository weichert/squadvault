from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

KEY = "scripts/gate_creative_surface_registry_parity_v1.sh"
VAL = "Creative Surface Registry parity gate (v1)"

def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write_if_changed(p: Path, s: str) -> bool:
    old = _read(p)
    if old == s:
        return False
    p.write_text(s, encoding="utf-8", newline="\n")
    return True

def _already_present(s: str) -> bool:
    return f'"{KEY}"' in s or f"'{KEY}'" in s

def _insert_desc_entry(s: str) -> str:
    # Supports:
    #   DESC: dict[str, str] = {
    #   DESC: Dict[str, str] = {
    #   DESC = {
    import re

    m = re.search(r"\bDESC\b[^\n=]*=\s*\{\s*", s)
    if not m:
        _die("could not locate DESC map assignment (expected 'DESC ... = {')")

    insert_at = m.end()

    # Determine indentation by looking for the first existing key line after the dict start.
    tail = s[insert_at:]
    indent = "    "
    for ln in tail.splitlines(True):
        stripped = ln.lstrip()
        if stripped.startswith(("'", '"')):
            indent = ln[: len(ln) - len(stripped)]
            break
        if stripped.startswith("}"):
            # empty dict edge-case
            indent = "    "
            break

    entry = f'{indent}"{KEY}": "{VAL}",\n'
    return s[:insert_at] + entry + s[insert_at:]

def main() -> int:
    if not TARGET.exists():
        _die(f"missing target patcher: {TARGET}")

    s = _read(TARGET)
    if _already_present(s):
        print("OK: DESC entry already present (noop)")
        return 0

    out = _insert_desc_entry(s)
    if not _already_present(out):
        _die("insert failed (key still missing)")

    changed = _write_if_changed(TARGET, out)
    if not changed:
        print("OK: target already canonical (noop)")
        return 0

    print(f"OK: added DESC entry for {KEY} in {TARGET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
