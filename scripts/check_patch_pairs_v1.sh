#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "==> Gate: patcher/wrapper pairing (v1)"
echo "    rule: scripts/patch_*.sh <-> scripts/_patch_*.py"
echo "    legacy exceptions: scripts/patch_pair_allowlist_v1.txt"

ALLOWLIST="scripts/patch_pair_allowlist_v1.txt"

# Verbosity: set SV_PATCH_PAIR_VERBOSE=1 to print allowlisted details.
SV_PATCH_PAIR_VERBOSE="${SV_PATCH_PAIR_VERBOSE:-0}"
allowlisted_count=0


is_allowlisted() {
  local path="$1"
  [ -f "$ALLOWLIST" ] || return 1
  grep -Fxq "$path" "$ALLOWLIST"
}

wrappers="$(git ls-files 'scripts/patch_*.sh' || true)"
patchers="$(git ls-files 'scripts/_patch_*.py' || true)"

missing_pairs=0

note_missing() {
  local src="$1"
  local expected="$2"

  if is_allowlisted "$src"; then
    allowlisted_count=$((allowlisted_count + 1))
    if [ "${SV_PATCH_PAIR_VERBOSE}" = "1" ]; then
      echo "ALLOWLISTED: missing pair for $src"
      echo "            expected: $expected"
    fi
    return 0
  fi

  echo "ERROR: missing pair for $src"
  echo "       expected: $expected"
  missing_pairs=1
}
}

# Wrapper -> patcher (avoid pipe subshell; bash 3.2 safe)
if [ -n "$wrappers" ]; then
  while IFS= read -r w; do
    [ -z "$w" ] && continue
    base="$(basename "$w")"           # patch_foo_v1.sh
    stem="${base%.sh}"               # patch_foo_v1
    expected="scripts/_${stem}.py"   # scripts/_patch_foo_v1.py
    if [ ! -f "$expected" ]; then
      note_missing "$w" "$expected"
    fi
  done <<< "$wrappers"
fi

# Patcher -> wrapper (avoid pipe subshell; bash 3.2 safe)
if [ -n "$patchers" ]; then
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="$(basename "$p")"          # _patch_foo_v1.py
    stem="${base%.py}"               # _patch_foo_v1
    if [ "${stem#_}" = "$stem" ]; then
      # Defensive: should never happen with our glob, but fail-closed.
      if is_allowlisted "$p"; then
        echo "ALLOWLISTED: unexpected patcher name (missing leading underscore): $p"
      else
        echo "ERROR: unexpected patcher name (missing leading underscore): $p"
        missing_pairs=1
      fi
      continue
    fi
    expected="scripts/${stem#_}.sh"  # scripts/patch_foo_v1.sh
    if [ ! -f "$expected" ]; then
      note_missing "$p" "$expected"
    fi
  done <<< "$patchers"
fi

if [ "$missing_pairs" -ne 0 ]; then
  echo "FAIL: patcher/wrapper pairing gate failed."
  echo "      Fix by adding the missing counterpart, or (rarely) allowlist the path:"
  echo "        $ALLOWLIST"
  exit 1
fi

if [ "$allowlisted_count" -ne 0 ] && [ "${SV_PATCH_PAIR_VERBOSE}" != "1" ]; then
  echo "OK: patcher/wrapper pairing gate passed. (allowlisted missing pairs: ${allowlisted_count}; suppressed; set SV_PATCH_PAIR_VERBOSE=1)"
else
  echo "OK: patcher/wrapper pairing gate passed."
fi
