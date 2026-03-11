#!/usr/bin/env bash
# SquadVault — Shared Status Helpers
# Purpose: Consistent, human-readable status output across scripts
# Scope: Bash-only, no side effects, safe to source multiple times

# Ensure UTF-8 (best-effort, non-fatal)
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

# Symbols
SV_OK="✅"
SV_FAIL="❌"
SV_WARN="⚠️"
SV_INFO="ℹ️"
SV_SKIP="⏭️"

# Formatting helpers
sv_ok()    { echo "${SV_OK} $*"; }
sv_fail()  { echo "${SV_FAIL} $*" >&2; }
sv_warn()  { echo "${SV_WARN} $*"; }
sv_info()  { echo "${SV_INFO} $*"; }
sv_skip()  { echo "${SV_SKIP} $*"; }

# Structured status line (scan-friendly)
# Usage: sv_status "Wk 7" PASS
sv_status() {
  local label="$1"
  local status="$2"

  case "$status" in
    PASS) echo "$label   ${SV_OK} PASS" ;;
    FAIL) echo "$label   ${SV_FAIL} FAIL" ;;
    WARN) echo "$label   ${SV_WARN} WARN" ;;
    SKIP) echo "$label   ${SV_SKIP} SKIPPED" ;;
    *)    echo "$label   ${SV_INFO} $status" ;;
  esac
}
