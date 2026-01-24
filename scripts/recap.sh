#!/bin/sh
# SquadVault — recap CLI shim (deterministic python path)
# Purpose: run the canonical scripts/recap.py via scripts/py to enforce repo imports.
#
# Example:
#   ./scripts/recap.sh check --db ... --league-id ... --season ... --week-index ...
#   ./scripts/recap.sh golden-path --db ... --league-id ... --season ... --week-index ... --approved-by ...

set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec "$ROOT/scripts/py" "$ROOT/scripts/recap.py" "$@"
