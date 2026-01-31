#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

GITIGNORE = Path(".gitignore")
NEEDLE = "scripts/_patch_fix_ops_orchestrate_wrapper_path_normalization_v1.py"

def main() -> None:
    if not GITIGNORE.exists():
        raise SystemExit("ERROR: .gitignore not found")

    text = GITIGNORE.read_text(encoding="utf-8")

    if NEEDLE in text:
        print("OK: .gitignore already allows ops_orchestrate path normalization patcher (v1).")
        return

    # Append in a conservative way: add a small allowlist block at end.
    # (No rewrites: only append if missing.)
    if not text.endswith("\n"):
        text += "\n"

    text += "\n# Ops: allowlisted patchers (v1)\n"
    text += f"!{NEEDLE}\n"

    GITIGNORE.write_text(text, encoding="utf-8")
    print("OK: patched .gitignore to allow ops_orchestrate path normalization patcher (v1).")

if __name__ == "__main__":
    main()
