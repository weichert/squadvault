#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate treat --commit no-op as OK (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python - <<'PY'
from __future__ import annotations
from pathlib import Path

p = Path("scripts/ops_orchestrate.sh")
s = p.read_text(encoding="utf-8")

marker = 'OK: --commit requested but no changes occurred (no-op); skipping commit'
if marker in s:
    print("OK: ops_orchestrate already allows --commit no-op (v3 no-op).")
    raise SystemExit(0)

lines = s.splitlines(True)

# Locate commit_enabled block start
start = None
for i, line in enumerate(lines):
    if line.strip() == 'if [[ "${commit_enabled}" == "1" ]]; then':
        start = i
        break
if start is None:
    raise SystemExit("ERROR: could not locate commit_enabled block header")

# Find outer 'fi' for commit_enabled block (track nesting)
depth = 0
end = None
for j in range(start, len(lines)):
    t = lines[j].lstrip()
    if t.startswith("if "):
        depth += 1
    elif t.startswith("fi"):
        depth -= 1
        if depth == 0:
            end = j
            break
if end is None:
    raise SystemExit("ERROR: could not locate end of commit_enabled block (fi)")

block = lines[start:end+1]

die_line = 'die "--commit requested but no changes occurred"'
die_idx = None
for idx, line in enumerate(block):
    if die_line in line:
        die_idx = idx
        break
if die_idx is None:
    raise SystemExit("ERROR: could not locate expected die(\"--commit requested but no changes occurred\")")

# We expect a structure like:
# if [[ "${pass1_changed}" != "1" ]]; then
#   die ...
# fi
# <commit body begins...>
# We'll transform into:
# if [[ "${pass1_changed}" != "1" ]]; then
#   echo "OK: ... skipping commit"
# else
#   <commit body>
# fi

# Replace the die line with echo
indent = block[die_idx].split("die", 1)[0]
block[die_idx] = f'{indent}echo "{marker}"\n'

# Find the 'fi' that closes the pass1_changed guard (after die line)
guard_fi_idx = None
for k in range(die_idx+1, len(block)):
    if block[k].lstrip().startswith("fi"):
        guard_fi_idx = k
        break
if guard_fi_idx is None:
    raise SystemExit("ERROR: could not locate guard fi after die line")

# Insert 'else' immediately after that guard fi
# (commit body begins right after)
else_indent = block[guard_fi_idx].split("fi", 1)[0]
block.insert(guard_fi_idx + 1, f"{else_indent}else\n")

# Now we must close this new if/else with a 'fi' just before the OUTER commit_enabled fi.
# The outer fi is currently the last line of block.
outer_fi_local = len(block) - 1
outer_indent = block[outer_fi_local].split("fi", 1)[0]
block.insert(outer_fi_local, f"{outer_indent}fi\n")

out = lines[:start] + block + lines[end+1:]
p.write_text("".join(out), encoding="utf-8")
print("OK: patched ops_orchestrate to treat --commit no-op as OK (v3).")
PY

echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
