#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REGISTRY="$REPO_ROOT/docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"
PROVE="$REPO_ROOT/scripts/prove_ci.sh"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

registry="$tmpdir/registry.txt"
executed="$tmpdir/executed.txt"

grep -o 'scripts/gate_[^[:space:]]*\.sh' "$REGISTRY" \
  | sed 's/[[:space:]]*$//' \
  | sort -u > "$registry"

# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v3_BEGIN
awk '
  /^[[:space:]]*(#|$)/ { next }

  {
    line = $0

    if (match(line, /^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)="[^"]*scripts\/gate_[^"]+\.sh"/)) {
      decl = substr(line, RSTART, RLENGTH)
      var_name = decl
      sub(/^[[:space:]]*/, "", var_name)
      sub(/=.*/, "", var_name)

      value = decl
      sub(/^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*="/, "", value)
      sub(/"$/, "", value)
      sub(/^\.\//, "", value)
      sub(/^.*scripts\//, "scripts/", value)

      vars[var_name] = value
      next
    }

    if (match(line, /^[[:space:]]*bash[[:space:]]+\.\/scripts\/gate_[^[:space:];|&()]+\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*bash[[:space:]]+/, "", path)
      sub(/[[:space:];|&()].*$/, "", path)
      sub(/^\.\//, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*bash[[:space:]]+scripts\/gate_[^[:space:];|&()]+\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*bash[[:space:]]+/, "", path)
      sub(/[[:space:];|&()].*$/, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*\.\/scripts\/gate_[^[:space:];|&()]+\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/[[:space:];|&()].*$/, "", path)
      sub(/^\.\//, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*scripts\/gate_[^[:space:];|&()]+\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/[[:space:];|&()].*$/, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*bash[[:space:]]+"\$[A-Za-z_][A-Za-z0-9_]*"([[:space:];|&()]|$)/)) {
      ref = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*bash[[:space:]]+"/, "", ref)
      sub(/".*$/, "", ref)
      sub(/^\$/, "", ref)
      if (ref in vars) {
        print vars[ref]
      }
      next
    }

    if (match(line, /^[[:space:]]*"\$[A-Za-z_][A-Za-z0-9_]*"([[:space:];|&()]|$)/)) {
      ref = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*"/, "", ref)
      sub(/".*$/, "", ref)
      sub(/^\$/, "", ref)
      if (ref in vars) {
        print vars[ref]
      }
      next
    }
  }
' "$PROVE" \
  | sort -u > "$executed"
# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v3_END



missing="$(comm -23 "$registry" "$executed" || true)"

if [ -n "$missing" ]; then
  echo "CI GUARDRAIL FAILURE: registry rows not executed by prove_ci.sh"
  echo
  echo "$missing"
  exit 1
fi

exit 0
