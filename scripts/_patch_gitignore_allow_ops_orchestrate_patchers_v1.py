#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

# Narrow allowlist: only ops_orchestrate fix patchers (not all patchers).
ALLOWLINE = "!scripts/_patch_fix_ops_orchestrate_*_v*.py"
HEADER = "# Ops: allowlist ops_orchestrate patchers (v1)"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    text = TARGET.read_text(encoding="utf-8")

    # Idempotency: if already present anywhere, no-op.
    if ALLOWLINE in text:
        print("OK: .gitignore already allows ops_orchestrate patchers (v1 no-op).")
        return

    # Minimal append: add a small block at end.
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + HEADER + "\n" + ALLOWLINE + "\n"

    TARGET.write_text(text, encoding="utf-8")
    print("OK: patched .gitignore to allow ops_orchestrate patchers (v1).")

if __name__ == "__main__":
    main()
