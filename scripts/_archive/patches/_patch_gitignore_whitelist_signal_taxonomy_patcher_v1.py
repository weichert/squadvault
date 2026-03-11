#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

TARGET_LINE = "!scripts/_patch_lock_signal_taxonomy_v1.py\n"

BLOCK_START = "# --- SquadVault: canonical patchers (MUST be tracked) ---"
BLOCK_END   = "# --- end canonical patchers ---"

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found at repo root.")

    s0 = GITIGNORE.read_text(encoding="utf-8")

    # Find canonical EOF block
    pat = re.compile(
        r"(\n# --- SquadVault: canonical patchers \(MUST be tracked\) ---\n)(.*?)(\n# --- end canonical patchers ---\n)",
        flags=re.S,
    )
    m = pat.search(s0)
    if not m:
        die("Canonical EOF unignore block not found in .gitignore.")

    head, body, tail = m.group(1), m.group(2), m.group(3)

    if TARGET_LINE.strip() in body:
        print("OK: .gitignore already whitelists _patch_lock_signal_taxonomy_v1.py; no changes.")
        return 0

    # Insert near other doc-lock patchers (stable + readable): append at end of body.
    body2 = body
    if not body2.endswith("\n") and body2 != "":
        body2 += "\n"
    body2 += TARGET_LINE

    s1 = s0[:m.start()] + head + body2 + tail + s0[m.end():]

    if s1 == s0:
        print("OK: no changes needed.")
        return 0

    GITIGNORE.write_text(s1, encoding="utf-8")
    print("OK: added whitelist for _patch_lock_signal_taxonomy_v1.py inside canonical EOF block.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
