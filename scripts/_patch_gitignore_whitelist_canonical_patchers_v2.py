#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

# We want to ensure this file is NOT ignored.
NEEDED = "!scripts/_patch_gitignore_whitelist_canonical_patchers_v1.py\n"

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found")

    s0 = GITIGNORE.read_text(encoding="utf-8")

    if NEEDED.strip() in s0:
        print("OK: .gitignore already whitelists _patch_gitignore_whitelist_canonical_patchers_v1.py; no changes.")
        return 0

    # Insert directly after the canonical patchers header if present, else append at end.
    anchor = "# Canonical patchers (DO track these)\n"
    if anchor in s0:
        s1 = s0.replace(anchor, anchor + NEEDED, 1)
    else:
        # Fallback: append with a small header (still deterministic/idempotent)
        s1 = s0
        if not s1.endswith("\n"):
            s1 += "\n"
        s1 += "\n# Canonical patchers (DO track these)\n" + NEEDED

    GITIGNORE.write_text(s1, encoding="utf-8")
    print("OK: updated .gitignore to whitelist _patch_gitignore_whitelist_canonical_patchers_v1.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
