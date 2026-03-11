#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

p = Path("scripts/check_shims_compliance.sh")
s0 = p.read_text(encoding="utf-8")

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

# Hard requirements
if not re.search(r'^\s*SCRIPT_DIR=', s0, flags=re.M):
    die("check_shims_compliance.sh missing SCRIPT_DIR= anchor. Refusing to patch.")
if not re.search(r'^\s*REPO_ROOT=', s0, flags=re.M):
    die("check_shims_compliance.sh missing REPO_ROOT= anchor. Refusing to patch.")

# Idempotency: if TARGET_SCRIPTS_DIR exists and there is no 'find scripts' left, we’re done.
has_target = bool(re.search(r'^\s*TARGET_SCRIPTS_DIR=', s0, flags=re.M))
has_find_scripts = ("find scripts " in s0) or ("find scripts\n" in s0) or ("find scripts\t" in s0)
if has_target and not has_find_scripts:
    print("OK: check_shims_compliance.sh already uses repo-root script paths; no changes.")
    raise SystemExit(0)

s = s0

# 1) Ensure TARGET_SCRIPTS_DIR exists right after REPO_ROOT line.
if not has_target:
    m = re.search(r'^(REPO_ROOT=.*\n)', s, flags=re.M)
    if not m:
        die("Expected REPO_ROOT line not found (unexpected). Refusing to patch.")
    s = s.replace(m.group(1), m.group(1) + 'TARGET_SCRIPTS_DIR="$REPO_ROOT/scripts"\n', 1)

# 2) Rewrite find scripts -> find "$TARGET_SCRIPTS_DIR"
# Do this only if present; refuse if nothing matches and still no TARGET usage.
before = s
s = s.replace("find scripts ", 'find "$TARGET_SCRIPTS_DIR" ')
s = s.replace("find scripts\t", 'find "$TARGET_SCRIPTS_DIR"\t')
s = s.replace("find scripts\n", 'find "$TARGET_SCRIPTS_DIR"\n')

# 3) Rewrite path segment scripts/ -> "$TARGET_SCRIPTS_DIR"/ conservatively
# Only when it appears as a path token (not inside words).
s = re.sub(r'(?<![\w/])scripts/', '"$TARGET_SCRIPTS_DIR"/', s)

# 4) Sanity: if we *still* have find scripts after patching, refuse (means unusual formatting)
if ("find scripts" in s):
    die("Still found 'find scripts' after attempted rewrite. Paste the find block for a tighter patcher.")

# 5) Ensure TARGET_SCRIPTS_DIR is actually present after modifications
if not re.search(r'^\s*TARGET_SCRIPTS_DIR="\$REPO_ROOT/scripts"\s*$', s, flags=re.M):
    die("TARGET_SCRIPTS_DIR anchor not present after patch. Refusing to write.")

if s == s0:
    print("OK: no changes needed.")
    raise SystemExit(0)

p.write_text(s, encoding="utf-8")
print("OK: patched check_shims_compliance.sh to use repo-root absolute scripts paths (TARGET_SCRIPTS_DIR).")
