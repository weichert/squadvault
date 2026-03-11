#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

fixture="fixtures/ci_squadvault.sqlite"
if [ ! -f "$fixture" ]; then
  echo "ERROR: fixture DB not found: $repo_root/$fixture"
  exit 1
fi

sha() {
python - <<'PY'
from __future__ import annotations
import hashlib
from pathlib import Path
p = Path("fixtures/ci_squadvault.sqlite")
print(hashlib.sha256(p.read_bytes()).hexdigest())
PY
}

before="$(sha)"

# Canonical CI runner must enforce temp working DB routing.
bash scripts/prove_ci.sh

after="$(sha)"

if [ "$before" != "$after" ]; then
  echo "ERROR: fixture DB was modified by CI proof run (immutable fixture invariant violated)"
  echo "fixture: $repo_root/$fixture"
  echo "before_sha256: $before"
  echo "after_sha256:  $after"
  echo
  echo "Restore with:"
  echo "  git restore --worktree fixtures/ci_squadvault.sqlite"
  exit 1
fi

exit 0
