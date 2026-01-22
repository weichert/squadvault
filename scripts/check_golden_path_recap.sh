#!/usr/bin/env bash
set -euo pipefail


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_status.sh"

# check_golden_path_recap.sh
#
# Golden Path validation for Weekly Recap Lifecycle v1
# - Uses recap.py list-weeks in JSON mode for week discovery
# - Uses recap.py status/check in JSON mode for per-week validation
#
# Auto-detects JSON flags supported by the CLI.
#
# NOTE: Use --debug-json in CI to persist JSON evidence for failed runs.
#
# Exit codes:
#   0 = all weeks pass
#   1 = at least one week fails
#   2 = usage / missing required args
#   3 = tool output / JSON parsing / capability error

set -euo pipefail
: "${HISTTIMEFORMAT:=}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/check_golden_path_recap.sh --db PATH --league-id ID --season YEAR [options]

Required:
  --db PATH
  --league-id ID
  --season YEAR

Optional:
  --start-week N        (inclusive)
  --end-week N          (inclusive)
  --recap-script PATH   (default: scripts/recap.py)
  --python PATH         (default: python)
  --pythonpath PATH     (default: src)
  --verbose
  --debug-json          (write captured JSON blobs to /tmp)
EOF
}

DB=""
LEAGUE_ID=""
SEASON=""
START_WEEK=""
END_WEEK=""
RECAP_SCRIPT="scripts/recap.py"
PYTHON_BIN="python"
PYTHONPATH_DIR="src"
VERBOSE="0"
DEBUG_JSON="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db) DB="${2:-}"; shift 2 ;;
    --league-id) LEAGUE_ID="${2:-}"; shift 2 ;;
    --season) SEASON="${2:-}"; shift 2 ;;
    --start-week) START_WEEK="${2:-}"; shift 2 ;;
    --end-week) END_WEEK="${2:-}"; shift 2 ;;
    --recap-script) RECAP_SCRIPT="${2:-}"; shift 2 ;;
    --python) PYTHON_BIN="${2:-}"; shift 2 ;;
    --pythonpath) PYTHONPATH_DIR="${2:-}"; shift 2 ;;
    --verbose) VERBOSE="1"; shift 1 ;;
    --debug-json) DEBUG_JSON="1"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$DB" || -z "$LEAGUE_ID" || -z "$SEASON" ]]; then
  echo "Missing required args." >&2
  usage
  exit 2
fi

if [[ ! -f "$RECAP_SCRIPT" ]]; then
  echo "recap script not found: $RECAP_SCRIPT" >&2
  exit 2
fi

log() {
  if [[ "$VERBOSE" == "1" ]]; then
    echo "$@" >&2
  fi
}

run_recap() {
  PYTHONPATH="$PYTHONPATH_DIR" "$PYTHON_BIN" -u "$RECAP_SCRIPT" "$@"
}

subhelp() {
  # Print help text for a subcommand (best-effort)
  run_recap "$1" -h 2>&1 || true
}

# Return 0 if help output contains a token
help_has() {
  local sub="$1"
  local token="$2"
  local h
  h="$(subhelp "$sub")"
  echo "$h" | grep -qE -- "$token"
}

# Determine JSON args for a subcommand.
# Echoes JSON args (may be multiple tokens) or empty string if none.
detect_json_args() {
  local sub="$1"

  # Prefer the explicit formatter contract (your CLI has this)
  if help_has "$sub" -- '--format([^a-zA-Z0-9_-]|$)'; then
    echo "--format json"
    return 0
  fi

  # Only fall back to --json if it's truly present as an option
  if help_has "$sub" -- '--json([^a-zA-Z0-9_-]|$)'; then
    echo "--json"
    return 0
  fi

  if help_has "$sub" -- '--output([^a-zA-Z0-9_-]|$)'; then
    echo "--output json"
    return 0
  fi
  if help_has "$sub" -- '--out([^a-zA-Z0-9_-]|$)'; then
    echo "--out json"
    return 0
  fi

  echo ""
  return 0
}

LIST_JSON_ARGS="$(detect_json_args "list-weeks")"
STATUS_JSON_ARGS="$(detect_json_args "status")"
CHECK_JSON_ARGS="$(detect_json_args "check")"

if [[ -z "$LIST_JSON_ARGS" ]]; then
  echo "ERROR: recap.py list-weeks does not appear to support JSON output." >&2
  echo "" >&2
  echo "list-weeks -h output:" >&2
  subhelp "list-weeks" >&2
  exit 3
fi

# For per-week, prefer status if it exists and has JSON, else check.
# We also detect whether the subcommand exists at all by trying -h.
STATUS_EXISTS="0"
CHECK_EXISTS="0"
if run_recap status -h >/dev/null 2>&1; then STATUS_EXISTS="1"; fi
if run_recap check -h >/dev/null 2>&1; then CHECK_EXISTS="1"; fi

PERWEEK_SUB=""
PERWEEK_JSON_ARGS=""

if [[ "$STATUS_EXISTS" == "1" && -n "$STATUS_JSON_ARGS" ]]; then
  PERWEEK_SUB="status"
  PERWEEK_JSON_ARGS="$STATUS_JSON_ARGS"
elif [[ "$CHECK_EXISTS" == "1" && -n "$CHECK_JSON_ARGS" ]]; then
  PERWEEK_SUB="check"
  PERWEEK_JSON_ARGS="$CHECK_JSON_ARGS"
else
  echo "ERROR: Neither 'status' nor 'check' appears to support JSON output." >&2
  echo "" >&2
  if [[ "$STATUS_EXISTS" == "1" ]]; then
    echo "status -h output:" >&2
    subhelp "status" >&2
    echo "" >&2
  fi
  if [[ "$CHECK_EXISTS" == "1" ]]; then
    echo "check -h output:" >&2
    subhelp "check" >&2
    echo "" >&2
  fi
  exit 3
fi

log "Detected list-weeks JSON args: $LIST_JSON_ARGS"
log "Detected per-week subcommand: $PERWEEK_SUB ($PERWEEK_JSON_ARGS)"

# ------------------------------------------------------------------------------
# 1) Discover weeks via list-weeks JSON
# ------------------------------------------------------------------------------

# Build list-weeks command args
LIST_ARGS=(list-weeks --db "$DB" --league-id "$LEAGUE_ID" --season "$SEASON")
if [[ -n "$START_WEEK" ]]; then LIST_ARGS+=(--start-week "$START_WEEK"); fi
if [[ -n "$END_WEEK" ]]; then LIST_ARGS+=(--end-week "$END_WEEK"); fi
# shellcheck disable=SC2206
LIST_ARGS+=($LIST_JSON_ARGS)

LIST_JSON=""
if ! LIST_JSON="$(run_recap "${LIST_ARGS[@]}" 2>/dev/null)"; then
  echo "ERROR: list-weeks in JSON mode failed." >&2
  echo "Tried: $RECAP_SCRIPT ${LIST_ARGS[*]}" >&2
  echo "" >&2
  echo "list-weeks -h output:" >&2
  subhelp "list-weeks" >&2
  exit 3
fi

log "list-weeks JSON bytes: ${#LIST_JSON}"

# Optional debug dump (only when explicitly requested)
TMP_LIST_WEEKS=""
if [[ "$DEBUG_JSON" == "1" ]]; then
  TMP_LIST_WEEKS="/tmp/squadvault_list_weeks_${LEAGUE_ID}_${SEASON}.json"
  printf '%s' "$LIST_JSON" > "$TMP_LIST_WEEKS"
  log "Wrote list-weeks JSON to: $TMP_LIST_WEEKS"
fi

# Lightweight schema introspection (verbose only; no file writes)
if [[ "$VERBOSE" == "1" ]]; then
  log "Top-level keys: $("$PYTHON_BIN" -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); print(", ".join(sorted(d.keys())) if isinstance(d,dict) else type(d).__name__)' <<<"$LIST_JSON")"
  log "weeks type/count: $("$PYTHON_BIN" -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); w=d.get("weeks") if isinstance(d,dict) else None; print(type(w).__name__, len(w) if isinstance(w,list) else "n/a")' <<<"$LIST_JSON")"
  log "first week keys: $("$PYTHON_BIN" -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); w=d.get("weeks") or []; x=w[0] if w else None; print(", ".join(sorted(x.keys())) if isinstance(x,dict) else type(x).__name__)' <<<"$LIST_JSON")"
fi

# Extract week indexes (week_index OR week OR wk)
WEEK_INDEXES="$(
  set +e
  out="$(
    printf '%s' "$LIST_JSON" | "$PYTHON_BIN" -c '
import json, sys
data = json.loads(sys.stdin.read() or "{}")
weeks = data.get("weeks", [])
idxs = []
for w in weeks:
  if not isinstance(w, dict):
    continue
  for k in ("week_index", "week", "wk"):
    if k in w and w[k] is not None:
      try:
        idxs.append(int(w[k]))
      except Exception:
        pass
      break
idxs = sorted(set(idxs))
print(" ".join(map(str, idxs)))
'
  )"
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    echo "ERROR: failed to parse/extract week indexes (rc=$rc)" >&2
    if [[ -n "${TMP_LIST_WEEKS:-}" ]]; then
      echo "See: $TMP_LIST_WEEKS" >&2
    fi
    echo "First 400 chars of JSON:" >&2
    echo "${LIST_JSON:0:400}" >&2
    exit 3
  fi
  printf '%s' "$out"
)"

log "Parsed week indexes: ${WEEK_INDEXES:-<empty>}"

if [[ -z "$WEEK_INDEXES" ]]; then
  echo "No weeks found (after bounds). Nothing to check." >&2
  exit 0
fi

# ------------------------------------------------------------------------------
# 2) Per-week validation via status/check JSON
# ------------------------------------------------------------------------------

FAILS=0
TOTAL=0

echo "Golden Path Recap Check"
echo "DB=$DB  League=$LEAGUE_ID  Season=$SEASON"
echo "Weeks: $WEEK_INDEXES"
echo "Per-week: $PERWEEK_SUB ($PERWEEK_JSON_ARGS)"
echo

for W in $WEEK_INDEXES; do
  TOTAL=$((TOTAL + 1))
  if [[ "$VERBOSE" == "1" ]]; then
    echo "Checking week $W ..." >&2
  fi

  PERWEEK_ARGS=("$PERWEEK_SUB" --db "$DB" --league-id "$LEAGUE_ID" --season "$SEASON" --week-index "$W")
  # shellcheck disable=SC2206
  PERWEEK_ARGS+=($PERWEEK_JSON_ARGS)

  STATUS_JSON=""
  if ! STATUS_JSON="$(run_recap "${PERWEEK_ARGS[@]}" 2>/dev/null)"; then
    echo "Wk $W  ❌ ERROR: $PERWEEK_SUB JSON mode failed" >&2
    echo "Tried: $RECAP_SCRIPT ${PERWEEK_ARGS[*]}" >&2
    FAILS=$((FAILS + 1))
    continue
  fi

  # Optional debug dump for status blobs (only when explicitly requested)
  if [[ "$DEBUG_JSON" == "1" ]]; then
    tmp="/tmp/squadvault_status_${LEAGUE_ID}_${SEASON}_wk${W}.json"
    printf '%s' "$STATUS_JSON" > "$tmp"
    log "Wrote status JSON (week $W) to: $tmp"
  fi

  RESULT="$(
    printf '%s' "$STATUS_JSON" | "$PYTHON_BIN" -c '
import json, sys

raw = sys.stdin.read().strip()
try:
  s = json.loads(raw) if raw else {}
except Exception as e:
  print(f"FAIL:bad_json:{e}")
  raise SystemExit(0)

def up(x):
  return (x or "").strip().upper() if isinstance(x, str) else (str(x).strip().upper() if x is not None else "")

def getd(obj, key):
  return obj.get(key) if isinstance(obj, dict) else None

recap_run = getd(s, "recap_run") or {}
latest = getd(s, "latest_artifact") or {}
approved = getd(s, "approved_artifact") or {}
week = getd(s, "week") or {}

run_state = up(getd(recap_run, "state"))
latest_state = up(getd(latest, "state"))
approved_state = up(getd(approved, "state"))

latest_fp = getd(latest, "selection_fingerprint")
approved_fp = getd(approved, "selection_fingerprint")

# Prefer week window, else artifact window
w_start = getd(week, "window_start") or getd(latest, "window_start") or getd(approved, "window_start")
w_end   = getd(week, "window_end")   or getd(latest, "window_end")   or getd(approved, "window_end")

withheld_reason = getd(latest, "withheld_reason")
problems = getd(s, "problems")

ok = True
reasons = []

rs = run_state if run_state else "MISSING"
ls = latest_state if latest_state else "MISSING"
aps = approved_state if approved_state else "MISSING"

if run_state != "APPROVED":
  ok = False
  reasons.append(f"run={rs}")

if latest_state != "APPROVED":
  ok = False
  reasons.append(f"latest={ls}")

if approved_state != "APPROVED":
  ok = False
  reasons.append(f"approved={aps}")

# Fingerprint consistency (only if both exist)
if latest_fp and approved_fp and latest_fp != approved_fp:
  ok = False
  reasons.append("fp_mismatch")

# Windows must exist
if not w_start or not w_end:
  ok = False
  reasons.append("window_missing")

# Withheld must not be present
if withheld_reason not in (None, "", False):
  ok = False
  reasons.append("withheld")

# Problems must be empty if present
if problems is not None and problems not in ([], {}, "", False, 0, None):
  ok = False
  reasons.append("problems")

print("PASS" if ok else "FAIL:" + "; ".join(reasons))
'
  )"

  if [[ "$RESULT" == "PASS" ]]; then
    printf "Wk %-2s  ✅ PASS\n" "$W"
  else
    printf "Wk %-2s  ❌ %s\n" "$W" "${RESULT#FAIL:}"
    FAILS=$((FAILS + 1))
  fi
done

echo
if [[ "$FAILS" -eq 0 ]]; then
  echo "✅ All $TOTAL week(s) passed golden path checks."
  exit 0
else
  echo "❌ $FAILS / $TOTAL week(s) failed golden path checks."
  exit 1
fi
