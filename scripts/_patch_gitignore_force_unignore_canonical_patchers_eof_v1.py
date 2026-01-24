#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

CANONICAL_UNIGNORE_BLOCK = """\n# --- SquadVault: canonical patchers (MUST be tracked) ---\n!scripts/_patch_create_minimal_documentation_map_v1.py\n!scripts/_patch_lock_ops_shim_cwd_contract_v1.py\n!scripts/_patch_gitignore_whitelist_canonical_patchers_v1.py\n!scripts/_patch_gitignore_whitelist_canonical_patchers_v2.py\n!scripts/_patch_gitignore_pin_whitelist_after_patch_glob_v1.py\n# --- end canonical patchers ---\n"""

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def strip_existing_block(s: str) -> str:
    # Remove any prior canonical block (strict, idempotent)
    pat = re.compile(
        r"\n# --- SquadVault: canonical patchers \(MUST be tracked\) ---\n.*?\n# --- end canonical patchers ---\n",
        flags=re.S,
    )
    return re.sub(pat, "\n", s)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found at repo root.")

    s0 = GITIGNORE.read_text(encoding="utf-8")
    s = strip_existing_block(s0).rstrip("\n") + "\n"

    # Append at EOF so it always wins vs earlier ignore globs.
    s1 = s + CANONICAL_UNIGNORE_BLOCK

    if s1 == s0:
        print("OK: .gitignore already has canonical EOF unignore block; no changes.")
        return 0

    GITIGNORE.write_text(s1, encoding="utf-8")
    print("OK: appended canonical EOF unignore block to .gitignore.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
