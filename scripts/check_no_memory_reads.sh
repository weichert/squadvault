#!/usr/bin/env bash
set -euo pipefail

matches="$(grep -RIn "FROM memory_events" src/ | grep -vE "canonicalize|sqlite_store.py" || true)"
if [[ -n "${matches}" ]]; then
  echo "${matches}"
  echo "ERROR: Downstream reads from memory_events are not allowed"
  exit 1
fi

echo "OK: No forbidden downstream reads from memory_events"

