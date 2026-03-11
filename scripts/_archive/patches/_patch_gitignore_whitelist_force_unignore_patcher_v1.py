#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

TARGET = "!scripts/_patch_gitignore_whitelist_force_unignore_patcher_v1.py"

BLOCK_START = "# --- SquadVault: canonical patchers (MUST be tracked) ---"
BLOCK_END   = "# --- end canonical patchers ---"

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found at repo root.")

    s0 = GITIGNORE.read_text(encoding="utf-8")

    # Must have canonical block (strict)
    start_i = s0.find(BLOCK_START)
    end_i = s0.find(BLOCK_END)
    if start_i == -1 or end_i == -1 or end_i < start_i:
        die("Canonical EOF block not found. Expected canonical patchers block markers.")

    # If already present anywhere, we’re done
    if re.search(rf"(?m)^{re.escape(TARGET)}\s*$", s0):
        print("OK: .gitignore already whitelists whitelist_force_unignore patcher; no changes.")
        return 0

    # Insert immediately before BLOCK_END (inside the block)
    insert_pos = s0.find(BLOCK_END, start_i)
    s1 = s0[:insert_pos] + TARGET + "\n" + s0[insert_pos:]

    GITIGNORE.write_text(s1, encoding="utf-8")
    print("OK: added whitelist for whitelist_force_unignore patcher inside canonical EOF block.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
