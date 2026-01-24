#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

GLOB_LINE = "scripts/_patch_*.py"
WHITELIST = [
    "!scripts/_patch_gitignore_whitelist_canonical_patchers_v1.py",
    "!scripts/_patch_gitignore_whitelist_canonical_patchers_v2.py",
    "!scripts/_patch_gitignore_pin_whitelist_after_patch_glob_v1.py",
]

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found")

    lines = GITIGNORE.read_text(encoding="utf-8").splitlines(True)

    # Find the *first* occurrence of the ignore glob line.
    idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == GLOB_LINE:
            idx = i
            break
    if idx is None:
        die(f"Did not find required ignore glob line: {GLOB_LINE}")

    # Remove any existing occurrences of our whitelist lines (we’ll reinsert in the right spot).
    stripped = [ln.rstrip("\n") for ln in lines]
    keep = []
    for ln in stripped:
        if ln in WHITELIST:
            continue
        keep.append(ln)

    # Rebuild with newline preservation (normalize to \n on write).
    out = []
    for i, ln in enumerate(keep):
        out.append(ln)
        if i == idx:
            # Ensure a blank line separation is NOT required; just insert directly after.
            for w in WHITELIST:
                out.append(w)

    new_text = "\n".join(out) + "\n"
    old_text = GITIGNORE.read_text(encoding="utf-8")

    if new_text == old_text:
        print("OK: .gitignore already pins whitelist lines immediately after scripts/_patch_*.py; no changes.")
        return 0

    GITIGNORE.write_text(new_text, encoding="utf-8")
    print("OK: updated .gitignore to pin whitelist lines immediately after scripts/_patch_*.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
