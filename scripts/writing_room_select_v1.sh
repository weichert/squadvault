#!/bin/sh
# SquadVault — Writing Room side-artifact gate (wrapper)
# Purpose: single blessed operator path for producing SelectionSetV1 via recap.py
#
# Example:
#   bash scripts/writing_room_select_v1.sh \
#     --db .local_squadvault.sqlite \
#     --league-id 70985 \
#     --season 2024 \
#     --week-index 6 \
#     --created-at-utc "2026-01-23T07:00:00Z"

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec "$ROOT/scripts/recap.py" check \
  --db "${DB:-.local_squadvault.sqlite}" \
  --league-id "${LEAGUE_ID:-70985}" \
  --season "${SEASON:-2024}" \
  --week-index "${WEEK_INDEX:-6}" \
  --enable-writing-room \
  --created-at-utc "${CREATED_AT_UTC:-2026-01-23T07:00:00Z}"
