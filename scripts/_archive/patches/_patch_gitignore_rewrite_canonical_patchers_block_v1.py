#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

BEGIN = "# --- SquadVault: canonical patchers (MUST be tracked) ---"
END = "# --- end canonical patchers ---"

BLOCK = "\n".join([
    "",
    BEGIN,
    "!scripts/_patch_create_minimal_documentation_map_v1.py",
    "!scripts/_patch_lock_ops_shim_cwd_contract_v1.py",
    "!scripts/_patch_gitignore_whitelist_canonical_patchers_v1.py",
    "!scripts/_patch_gitignore_whitelist_canonical_patchers_v2.py",
    "!scripts/_patch_gitignore_pin_whitelist_after_patch_glob_v1.py",
    "!scripts/_patch_gitignore_force_unignore_canonical_patchers_eof_v1.py",
    "!scripts/_patch_gitignore_whitelist_force_unignore_patcher_v1.py",
    "!scripts/_patch_gitignore_rewrite_canonical_patchers_block_v1.py",
    END,
    "",
])

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def strip_block(s: str) -> str:
    pat = re.compile(
        r"\n" + re.escape(BEGIN) + r"\n.*?\n" + re.escape(END) + r"\n",
        flags=re.S,
    )
    return re.sub(pat, "\n", s)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found at repo root.")

    s0 = GITIGNORE.read_text(encoding="utf-8")

    # Remove any existing canonical block (even if corrupted inside).
    s = strip_block(s0).rstrip("\n") + "\n"

    # Append a fresh canonical block at EOF so it always wins vs earlier ignore globs.
    s1 = s + BLOCK

    if s1 == s0:
        print("OK: .gitignore canonical patchers block already clean; no changes.")
        return 0

    GITIGNORE.write_text(s1, encoding="utf-8")
    print("OK: rewrote canonical patchers EOF block in .gitignore (clean).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
