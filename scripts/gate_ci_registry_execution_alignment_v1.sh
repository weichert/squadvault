#!/usr/bin/env bash
# SquadVault — CI Registry → Execution Alignment Gate (v1)
#
# Fails closed if:
#  - A registered proof runner is not executed by scripts/prove_ci.sh (unless explicitly exempted)
#  - A proof runner is executed by scripts/prove_ci.sh but not registered
#  - A registered proof runner is only executed conditionally without an explicit allow-marker
#
# Sources of truth:
#  - Registry: docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md
#  - Execution: scripts/prove_ci.sh
#
# Exception mechanism (explicit + marker-bounded + documented):
#  - Registry exemption block:
#      <!-- SV_CI_EXECUTION_EXEMPT_v1_BEGIN -->
#      scripts/prove_local_only_example.sh # reason
#      <!-- SV_CI_EXECUTION_EXEMPT_v1_END -->
#
# Conditional invocation allowlist (explicit + marker-bounded):
#  - In scripts/prove_ci.sh, wrap any conditional invocation with:
#      # SV_CI_EXECUTION_CONDITIONAL_OK_v1_BEGIN scripts/prove_foo.sh
#      ... (conditional block containing an invocation)
#      # SV_CI_EXECUTION_CONDITIONAL_OK_v1_END scripts/prove_foo.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

REGISTRY="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
EXEC="scripts/prove_ci.sh"

if [[ ! -f "${REGISTRY}" ]]; then
  echo "ERROR: missing registry: ${REGISTRY}" >&2
  exit 2
fi
if [[ ! -f "${EXEC}" ]]; then
  echo "ERROR: missing execution script: ${EXEC}" >&2
  exit 2
fi

tmp_dir=""
cleanup() {
  if [[ -n "${tmp_dir}" && -d "${tmp_dir}" ]]; then
    rm -rf "${tmp_dir}"
  fi
}
trap cleanup EXIT

tmp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t sv_ci_align)"

R_ALL="${tmp_dir}/registered_all.txt"
X_EXEMPT="${tmp_dir}/exempt.txt"
E_ALL="${tmp_dir}/executed_all.txt"
E_UNCOND="${tmp_dir}/executed_uncond.txt"
E_COND="${tmp_dir}/executed_cond.txt"
COND_ALLOW="${tmp_dir}/cond_allow.txt"

missing="${tmp_dir}/missing.txt"
extra="${tmp_dir}/extra.txt"
cond_bad="${tmp_dir}/cond_bad.txt"

echo "==> Gate: CI registry → execution alignment (v1)"
echo "    Registry: ${REGISTRY}"
echo "    Exec:     ${EXEC}"

# --- Extract registered proofs (R) ---
# Pull all occurrences of scripts/prove_*.sh anywhere in registry (sorted unique).
grep -oE 'scripts/prove_[A-Za-z0-9_.-]+\.sh' "${REGISTRY}" | sort -u > "${R_ALL}" || true

if [[ ! -s "${R_ALL}" ]]; then
  echo "ERROR: registry parse produced empty proof list (expected scripts/prove_*.sh entries)" >&2
  exit 3
fi

# --- Extract exemptions (X) from a marker-bounded block in registry ---
# If markers don't exist, exemptions are empty (fail-closed still applies).
awk '
  BEGIN {inblk=0}
  /SV_CI_EXECUTION_EXEMPT_v1_BEGIN/ {inblk=1; next}
  /SV_CI_EXECUTION_EXEMPT_v1_END/ {inblk=0; next}
  inblk {print}
' "${REGISTRY}" \
| grep -oE 'scripts/prove_[A-Za-z0-9_.-]+\.sh' \
| sort -u > "${X_EXEMPT}" || true

# --- Extract conditional allowlist markers from prove_ci.sh ---
# Lines must be exactly:
#   # SV_CI_EXECUTION_CONDITIONAL_OK_v1_BEGIN scripts/prove_foo.sh
#   # SV_CI_EXECUTION_CONDITIONAL_OK_v1_END scripts/prove_foo.sh
# We treat the BEGIN markers as the allowlist declarations.
grep -nE '^[[:space:]]*#[[:space:]]*SV_CI_EXECUTION_CONDITIONAL_OK_v1_BEGIN[[:space:]]+scripts/prove_[A-Za-z0-9_.-]+\.sh[[:space:]]*$' "${EXEC}" \
| sed -E 's/.*SV_CI_EXECUTION_CONDITIONAL_OK_v1_BEGIN[[:space:]]+//; s/[[:space:]]*$//' \
| sort -u > "${COND_ALLOW}" || true

# --- Extract executed proofs (E), while tracking conditional depth ---
# We do a conservative block-depth tracker for if/fi, case/esac, for/done, while/done, until/done.
# Any invocation at depth>0 is considered conditional.
#
# Invocation shapes matched:
#   bash scripts/prove_foo.sh
#   bash ./scripts/prove_foo.sh
#   ./scripts/prove_foo.sh
#   scripts/prove_foo.sh  (rare; still count if appears as a command token)
awk '
  function ltrim(s){ sub(/^[ \t\r\n]+/,"",s); return s }
  function rtrim(s){ sub(/[ \t\r\n]+$/,"",s); return s }
  function trim(s){ return rtrim(ltrim(s)) }

  BEGIN {
    depth=0
  }

  {
    raw=$0
    # drop comments (conservative)
    line=raw
    sub(/[[:space:]]*#.*/,"",line)
    line=trim(line)

    # adjust depth based on control structures
    # incrementers (conservative patterns)
    if (line ~ /(^|[;[:space:]])if([[:space:]]|\()/) {
      depth++
    }
    if (line ~ /(^|[;[:space:]])case([[:space:]]|\()/) {
      depth++
    }
    if (line ~ /(^|[;[:space:]])for([[:space:]]|\()/) {
      depth++
    }
    if (line ~ /(^|[;[:space:]])while([[:space:]]|\()/) {
      depth++
    }
    if (line ~ /(^|[;[:space:]])until([[:space:]]|\()/) {
      depth++
    }

    # capture invocations of scripts/prove_*.sh on this line
    # match path token with optional leading ./ and optional bash
    if (match(line, /(bash[[:space:]]+)?(\.\/)?scripts\/prove_[A-Za-z0-9_.-]+\.sh/)) {
      tok=substr(line, RSTART, RLENGTH)
      gsub(/^bash[[:space:]]+/,"",tok)
      gsub(/^\.\//,"",tok)
      print NR "\t" depth "\t" tok
    }

    # decrementers after processing line (so single-line structures still count conditional)
    if (line ~ /(^|[;[:space:]])fi([;[:space:]]|$)/) {
      if (depth > 0) depth--
    }
    if (line ~ /(^|[;[:space:]])esac([;[:space:]]|$)/) {
      if (depth > 0) depth--
    }
    if (line ~ /(^|[;[:space:]])done([;[:space:]]|$)/) {
      if (depth > 0) depth--
    }
  }
' "${EXEC}" > "${tmp_dir}/exec_hits.tsv" || true

cut -f3 "${tmp_dir}/exec_hits.tsv" | sort -u > "${E_ALL}" || true
awk -F'\t' '$2 == 0 {print $3}' "${tmp_dir}/exec_hits.tsv" | sort -u > "${E_UNCOND}" || true
awk -F'\t' '$2 > 0 {print $1 ":" $3}' "${tmp_dir}/exec_hits.tsv" | sort -u > "${E_COND}" || true

# SV_PATCH: exclude prove_ci from gate sets (v1) begin

# Exclude orchestrator (prove_ci.sh) from all derived sets.
# This gate is about *proof runners* registered in the registry vs invoked by prove_ci.sh.
filter_out_prove_ci() {
  # $1 = file; $2 = mode ("plain" or "cond")
  f="$1"
  mode="${2:-plain}"
  if [[ ! -f "$f" ]]; then
    return
  fi
  if [[ "$mode" = "cond" ]]; then
    # lines like: <line>:scripts/prove_foo.sh
    grep -vE ":scripts/prove_ci\.sh$" "$f" > "${f}.tmp" || true
  else
    grep -vE "^scripts/prove_ci\.sh$" "$f" > "${f}.tmp" || true
  fi
  mv "${f}.tmp" "$f"
}

# Apply to all sets we derive.
filter_out_prove_ci "${R_ALL}" plain
filter_out_prove_ci "${X_EXEMPT}" plain
filter_out_prove_ci "${COND_ALLOW}" plain
filter_out_prove_ci "${E_ALL}" plain
filter_out_prove_ci "${E_UNCOND}" plain
filter_out_prove_ci "${E_COND}" cond

# SV_PATCH: exclude prove_ci from gate sets (v1) end
if [[ ! -s "${E_ALL}" ]]; then
  echo "ERROR: could not find any proof runner invocations in ${EXEC}" >&2
  echo "HINT: expected lines like: bash scripts/prove_foo.sh" >&2
  exit 4
fi

# --- Compute missing / extra ---
# missing = (R - X) - E
comm -23 <(comm -23 "${R_ALL}" "${X_EXEMPT}") "${E_ALL}" > "${missing}" || true
# extra = E - R
comm -23 "${E_ALL}" "${R_ALL}" > "${extra}" || true

# --- Conditional invocation must be explicitly allowlisted ---
# For each conditional hit "line:scripts/prove_x.sh":
#  - if scripts/prove_x.sh is in allowlist => OK
#  - else => fail
awk -F':' '
  NR==FNR {allow[$0]=1; next}
  {
    path=$2
    if (!(path in allow)) print $0
  }
' "${COND_ALLOW}" "${E_COND}" > "${cond_bad}" || true

fail=0

if [[ -s "${missing}" ]]; then
  fail=1
  echo
  echo "FAIL: Registered but not executed (and not exempted):"
  sed 's/^/  - /' "${missing}"
fi

if [[ -s "${extra}" ]]; then
  fail=1
  echo
  echo "FAIL: Executed but not registered:"
  sed 's/^/  - /' "${extra}"
fi

if [[ -s "${cond_bad}" ]]; then
  fail=1
  echo
  echo "FAIL: Conditionally invoked without explicit allow marker:"
  echo "      Format: prove_ci.sh:<line>:scripts/prove_*.sh"
  sed 's/^/  - /' "${cond_bad}"
  echo
  echo "HINT: Wrap the conditional invocation with marker-bounded allowlist lines:"
  echo "  # SV_CI_EXECUTION_CONDITIONAL_OK_v1_BEGIN scripts/prove_foo.sh"
  echo "  ... conditional block containing invocation ..."
  echo "  # SV_CI_EXECUTION_CONDITIONAL_OK_v1_END scripts/prove_foo.sh"
fi

if [[ "${fail}" -ne 0 ]]; then
  echo
  echo "Gate result: FAIL (v1)"
  exit 1
fi

echo "Gate result: PASS (v1)"
