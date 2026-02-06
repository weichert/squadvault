#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: ops_orchestrate treat --commit no-op as OK (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python - <<'PY'
from __future__ import annotations
from pathlib import Path

p = Path("scripts/ops_orchestrate.sh")
s = p.read_text(encoding="utf-8")
marker = 'echo "OK: --commit requested but no changes occurred (no-op); skipping commit"'

if marker in s:
    print("OK: ops_orchestrate already allows --commit no-op (v2 no-op).")
    raise SystemExit(0)

lines = s.splitlines(True)

start = None
for i, line in enumerate(lines):
    if line.strip() == 'if [[ "${commit_enabled}" == "1" ]]; then':
        start = i
        break

if start is None:
    raise SystemExit("ERROR: could not locate commit_enabled block header")

# find matching 'fi' for this if (simple nesting counter)
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

block = lines[start : end + 1]
needle = 'die "--commit requested but no changes occurred"'
if not any(needle in x for x in block):
    raise SystemExit("ERROR: commit_enabled block found, but expected die(...) line not present")

# Find the commit section start (we preserve it verbatim)
commit_anchor = 'echo "=== Commit (explicit) ==="'
k = None
for idx, line in enumerate(block):
    if commit_anchor in line:
        k = idx
        break
if k is None:
    raise SystemExit("ERROR: could not locate commit section anchor inside commit_enabled block")

commit_section = block[k : -1]  # up to (but excluding) the final 'fi' of the outer block

new_block = []
new_block.append('if [[ "${commit_enabled}" == "1" && "${pass1_changed}" == "1" ]]; then\n')
new_block.extend(commit_section)
new_block.append('elif [[ "${commit_enabled}" == "1" ]]; then\n')
new_block.append('  echo "OK: --commit requested but no changes occurred (no-op); skipping commit"\n')
new_block.append("fi\n")

out = lines[:start] + new_block + lines[end+1:]
p.write_text("".join(out), encoding="utf-8")
print("OK: patched ops_orchestrate to treat --commit no-op as OK (v2).")
PY

echo "==> bash syntax check"
bash -n scripts/ops_orchestrate.sh
echo "OK"
