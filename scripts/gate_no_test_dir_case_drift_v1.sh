#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

upper="Tests"
lower="tests"

upper_exists=0
lower_exists=0
[ -e "$upper" ] && upper_exists=1
[ -e "$lower" ] && lower_exists=1

if [ "$upper_exists" -eq 0 ] && [ "$lower_exists" -eq 0 ]; then
  echo "ERROR: no tests directory found (neither Tests/ nor tests/)."
  exit 1
fi

# If both exist, allow only if they are the SAME inode (case-insensitive FS alias).
if [ "$upper_exists" -eq 1 ] && [ "$lower_exists" -eq 1 ]; then
  same_inode="$(python - <<'PY'
from __future__ import annotations
import os
u = os.stat("Tests")
l = os.stat("tests")
print("1" if (u.st_dev, u.st_ino) == (l.st_dev, l.st_ino) else "0")
PY
)"
  if [ "$same_inode" != "1" ]; then
    echo "ERROR: test dir case drift detected: Tests/ and tests/ are distinct directories."
    echo "Choose ONE canonical tests directory and remove the other."
    exit 1
  fi
fi

# Fail-closed if git tracks BOTH spellings (breaks on case-insensitive FS).
tracked_upper="$(git ls-files | grep -E '^Tests/' | head -n 1 || true)"
tracked_lower="$(git ls-files | grep -E '^tests/' | head -n 1 || true)"

if [ -n "$tracked_upper" ] && [ -n "$tracked_lower" ]; then
  echo "ERROR: git tracks both Tests/ and tests/ paths (case drift in index)."
  echo "Normalize to ONE spelling in the git index."
  exit 1
fi

if [ -n "$tracked_upper" ]; then
  echo "OK: canonical tests directory (git-tracked): Tests/"
  exit 0
fi

if [ -n "$tracked_lower" ]; then
  echo "OK: canonical tests directory (git-tracked): tests/"
  exit 0
fi

# If neither spelling is tracked (unexpected), accept the one that exists.
if [ "$lower_exists" -eq 1 ]; then
  echo "OK: canonical tests directory (untracked): tests/"
  exit 0
fi

echo "OK: canonical tests directory (untracked): Tests/"
exit 0
