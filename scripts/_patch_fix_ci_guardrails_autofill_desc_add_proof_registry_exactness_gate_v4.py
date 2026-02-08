from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

NEW_KEY = "scripts/gate_ci_proof_surface_registry_exactness_v1.sh"
NEW_DESC = "CI Proof Surface Registry exactness: enforce machine-managed list matches tracked scripts/prove_*.sh (v1)"

DESC_ASSIGN_RE = re.compile(r"(?m)^(?P<indent>\s*)DESC\b[^=]*=\s*\{")

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")

    if re.search(rf'["\']{re.escape(NEW_KEY)}["\']\s*:', text):
        print("OK: DESC entry already present (no-op).")
        return 0

    m = DESC_ASSIGN_RE.search(text)
    if not m:
        print("ERROR: could not locate DESC dict assignment.", file=sys.stderr)
        return 1

    indent = m.group("indent")
    entry_indent = indent + "    "

    close_re = re.compile(rf"(?m)^{re.escape(indent)}\}}\s*$")
    close_m = close_re.search(text, pos=m.end())
    if not close_m:
        print("ERROR: could not find closing brace for DESC dict.", file=sys.stderr)
        return 1

    insert = f'{entry_indent}"{NEW_KEY}": "{NEW_DESC}",\n'
    updated = text[: close_m.start()] + insert + text[close_m.start() :]

    if updated != text:
        TARGET.write_text(updated, encoding="utf-8")
        print(f"UPDATED: {TARGET}")
    else:
        print("OK: no changes needed.")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
