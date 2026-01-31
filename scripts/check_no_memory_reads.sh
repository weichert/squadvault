#!/usr/bin/env bash
set -euo pipefail

echo "=== Check: no forbidden downstream reads from memory_events ==="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# If you want this to be strict, keep this allowlist SMALL and explicit.
# These are the *only* files allowed to reference memory_events.
ALLOWLIST=(
  "src/squadvault/core/recaps/render/render_deterministic_facts_block_v1.py"
  "src/squadvault/consumers/recap_generate.py"
  "src/squadvault/consumers/recap_week_enrich_artifact.py"
  "src/squadvault/consumers/recap_week_gating_check.py"
  "src/squadvault/consumers/recap_range_preview.py"
  "src/squadvault/consumers/recap_week_diagnose_empty.py"
)

# Build a grep -v -f filter file from the allowlist (exact path matches)
tmp="$(mktemp)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

for f in "${ALLOWLIST[@]}"; do
  # Anchor the match to "path:" prefix emitted by grep -n
  echo "^${f}:" >> "$tmp"
done

# Scan for direct SQL reads from memory_events
# (you can broaden this pattern later; keep it simple now)
hits="$(
  grep -RIn --line-number -e "FROM memory_events" src \
    | grep -v -f "$tmp" \
    || true
)"

if [[ -n "$hits" ]]; then
  echo "$hits"
  echo "❌ Downstream reads from memory_events are not allowed (outside allowlist)" >&2
  exit 1
fi

echo "OK: no forbidden memory_events reads"
