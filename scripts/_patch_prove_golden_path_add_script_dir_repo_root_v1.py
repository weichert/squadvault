#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

p = Path("scripts/prove_golden_path.sh")
s0 = p.read_text(encoding="utf-8")

# Idempotency: if anchors already present, do nothing.
if re.search(r'^\s*SCRIPT_DIR=', s0, flags=re.M) and re.search(r'^\s*REPO_ROOT=', s0, flags=re.M):
    print("OK: prove_golden_path.sh already has SCRIPT_DIR + REPO_ROOT; no changes.")
    raise SystemExit(0)

# Refuse if only one anchor exists (mixed state) — we want deterministic inserts.
has_sd = bool(re.search(r'^\s*SCRIPT_DIR=', s0, flags=re.M))
has_rr = bool(re.search(r'^\s*REPO_ROOT=', s0, flags=re.M))
if has_sd or has_rr:
    raise SystemExit(
        "ERROR: prove_golden_path.sh has partial anchor state (only one of SCRIPT_DIR/REPO_ROOT).\n"
        "Refusing to patch to avoid double-inserts. Normalize manually OR paste top-of-file here."
    )

lines = s0.splitlines(True)
if not lines or not lines[0].startswith("#!"):
    raise SystemExit("ERROR: prove_golden_path.sh missing shebang line. Refusing to patch.")

# Insert after:
# - shebang
# - contiguous comment lines
# - optional blank line
# - optional `set -...` line(s) (we insert AFTER set lines, so anchors are available to the rest)
i = 1

# consume comment-only header lines immediately after shebang
while i < len(lines) and (lines[i].startswith("#") or lines[i].strip() == ""):
    # Stop if we hit a non-comment, non-empty line
    if not lines[i].startswith("#") and lines[i].strip() != "":
        break
    i += 1

# consume contiguous set lines (common in your scripts)
while i < len(lines) and re.match(r'^\s*set\s+-', lines[i]):
    i += 1

insert = (
    'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
    'REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"\n'
    "\n"
)

s1 = "".join(lines[:i] + [insert] + lines[i:])

# Safety: refuse if we somehow didn’t change content
if s1 == s0:
    raise SystemExit("ERROR: no changes made (unexpected). Refusing to write.")

p.write_text(s1, encoding="utf-8")
print("OK: inserted SCRIPT_DIR + REPO_ROOT anchors into prove_golden_path.sh")
