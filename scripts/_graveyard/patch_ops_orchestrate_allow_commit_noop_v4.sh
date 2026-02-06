#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate treat --commit no-op as OK (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python - <<'PY'
from __future__ import annotations
from pathlib import Path

p = Path("scripts/ops_orchestrate.sh")
s = p.read_text(encoding="utf-8")
lines = s.splitlines(True)

marker = 'OK: --commit requested but no changes occurred (no-op); skipping commit'
if marker in s:
    print("OK: ops_orchestrate already allows --commit no-op (v4 no-op).")
    raise SystemExit(0)

# Find commit_enabled block start
commit_if = 'if [[ "${commit_enabled}" == "1" ]]; then'
start = next((i for i,l in enumerate(lines) if l.strip() == commit_if), None)
if start is None:
    raise SystemExit("ERROR: could not locate commit_enabled block header")

# Find matching outer fi for commit_enabled block
depth = 0
outer_end = None
for j in range(start, len(lines)):
    t = lines[j].lstrip()
    if t.startswith("if "):
        depth += 1
    elif t.startswith("fi"):
        depth -= 1
        if depth == 0:
            outer_end = j
            break
if outer_end is None:
    raise SystemExit("ERROR: could not locate end of commit_enabled block (fi)")

block = lines[start:outer_end+1]

# Find inner pass1_changed guard if
guard_if = 'if [[ "${pass1_changed}" != "1" ]]; then'
g_start = next((i for i,l in enumerate(block) if l.strip() == guard_if), None)
if g_start is None:
    raise SystemExit("ERROR: could not locate pass1_changed guard if")

die_line = 'die "--commit requested but no changes occurred"'
die_idx = next((i for i,l in enumerate(block) if die_line in l), None)
if die_idx is None:
    raise SystemExit("ERROR: could not locate expected die(\"--commit requested but no changes occurred\")")

# Find the guard fi that closes the pass1_changed if (first fi after die)
g_fi = None
for k in range(die_idx+1, len(block)):
    if block[k].lstrip().startswith("fi"):
        g_fi = k
        break
if g_fi is None:
    raise SystemExit("ERROR: could not locate guard fi after die line")

# Commit body currently begins after that guard fi and ends before outer fi
commit_body_start = g_fi + 1
commit_body_end = len(block) - 1  # index of outer fi
commit_body = block[commit_body_start:commit_body_end]

# Replace die line with echo marker
indent = block[die_idx].split("die", 1)[0]
block[die_idx] = f'{indent}echo "{marker}"\n'

# Build new block:
# - keep everything up through the die_idx line (inclusive)
# - insert "else"
# - insert commit body
# - close inner if with "fi"
# - then outer fi
prefix = block[:die_idx+1]

# Indent of guard_if line used for else/fi
guard_indent = block[g_start].split("if", 1)[0]

new_block = []
new_block.extend(prefix)
new_block.append(f"{guard_indent}else\n")
new_block.extend(commit_body)
new_block.append(f"{guard_indent}fi\n")
new_block.append(block[-1])  # outer fi

out = lines[:start] + new_block + lines[outer_end+1:]
p.write_text("".join(out), encoding="utf-8")
print("OK: patched ops_orchestrate to treat --commit no-op as OK (v4).")
PY

echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
