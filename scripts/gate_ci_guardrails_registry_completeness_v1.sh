#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REGISTRY="$REPO_ROOT/docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"
PROVE="$REPO_ROOT/scripts/prove_ci.sh"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

registry="$tmpdir/registry.txt"
executed="$tmpdir/executed.txt"

grep 'scripts/gate_.*\.sh' "$REGISTRY" \
  | sed 's/[[:space:]]*$//' \
  | sort -u > "$registry"

grep '^bash scripts/gate_.*\.sh$' "$PROVE" \
  | sed 's/^bash //' \
  | sed 's/[[:space:]]*$//' \
  | sort -u > "$executed"

missing="$(comm -23 "$registry" "$executed" || true)"

if [ -n "$missing" ]; then
  echo "CI GUARDRAIL FAILURE: registry rows not executed by prove_ci.sh"
  echo
  echo "$missing"
  exit 1
fi

exit 0
