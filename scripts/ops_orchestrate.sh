#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/ops_orchestrate.sh [--commit -m "message"] [--] <patch_wrapper.sh> [more_wrappers...]

Examples:
  ./scripts/ops_orchestrate.sh ./scripts/patch_docs_housekeeping_v1.sh
  ./scripts/ops_orchestrate.sh --commit -m "Ops: apply docs + CI hardening patches" \
    ./scripts/patch_a.sh ./scripts/patch_b.sh

Env:
  SV_DEBUG=1    Enable more verbose logging (never changes behavior).

Hard guarantees:
  - Refuses to run if git working tree is dirty (before/after).
  - Re-runs the patch chain and requires no changes (idempotency).
  - Always runs ./scripts/prove_ci.sh at the end.
EOF
}

note() {
  if [[ "${SV_DEBUG:-0}" == "1" ]]; then
    echo "NOTE: $*" >&2
  fi
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

# Resolve script dir robustly (bash 3.2; safe even if BASH_SOURCE is unset)
_script="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "${_script}")" && pwd)"

# Determine repo root via git (more reliable than SCRIPT_DIR/..)
cd "${SCRIPT_DIR}/.."
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "${REPO_ROOT}" ]] || die "could not determine git toplevel from ${SCRIPT_DIR}/.."
cd "${REPO_ROOT}"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || die "not inside a git work tree: ${REPO_ROOT}"

commit_enabled="0"
commit_msg=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --commit) commit_enabled="1"; shift ;;
    -m) shift; [[ $# -gt 0 ]] || die "-m requires a commit message"; commit_msg="$1"; shift ;;
    --) shift; break ;;
    -*) die "unknown flag: $1 (use --help)" ;;
    *) break ;;
  esac
done

[[ $# -ge 1 ]] || { usage; die "no patch wrappers provided"; }

if [[ "${commit_enabled}" == "1" && -z "${commit_msg}" ]]; then
  die "--commit requires -m \"commit message\""
fi

if ! git diff --quiet; then die "working tree has unstaged changes (refusing to run)"; fi
if ! git diff --cached --quiet; then die "index has staged changes (refusing to run)"; fi
if [[ -n "$(git status --porcelain)" ]]; then
  die "working tree not clean (including untracked files) (refusing to run)"
fi

start_head="$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")"
note "start HEAD: ${start_head}"
note "repo root: ${REPO_ROOT}"

run_chain() {
  local pass_label="$1"; shift
  local wrapper
  echo "=== Ops Orchestrator: ${pass_label} ==="

  for wrapper in "$@"; do
    local wpath="$wrapper"
    if [[ "${wpath}" != /* ]]; then
      wpath="${REPO_ROOT}/${wpath}"
    fi

    # Canonicalize path to remove ./ and ../ (bash 3.2 safe)
    local wdir wbase
    wdir="$(cd "$(dirname "${wpath}")" && pwd)"
    wbase="$(basename "${wpath}")"
    wpath="${wdir}/${wbase}"

    [[ -f "${wpath}" ]] || die "patch wrapper not found: ${wrapper}"
    [[ -x "${wpath}" ]] || die "patch wrapper not executable: ${wrapper} (chmod +x required)"

    case "${wpath}" in
      "${REPO_ROOT}/scripts/"*) ;;
      *) die "wrapper is outside scripts/: ${wrapper}" ;;
    esac

    echo "==> run: ${wrapper}"
    "${wpath}"
  done
}

changed_after_pass() {
  [[ -n "$(git status --porcelain)" ]]
}

summarize_changes() {
  echo "==> changes detected"
  git status --porcelain
  if [[ "${SV_DEBUG:-0}" == "1" ]]; then
    echo
    echo "==> git diff (debug)"
    git diff
    echo
    echo "==> git diff --cached (debug)"
    git diff --cached
  fi
}

run_chain "pass1" "$@"

pass1_changed="0"
if changed_after_pass; then
  pass1_changed="1"
  summarize_changes
else
  echo "==> no changes"
fi

# Snapshot the diff state after pass1 for idempotency verification.
pass1_diff="$(git diff)"
pass1_diff_cached="$(git diff --cached)"

run_chain "pass2 (idempotency check)" "$@"

# Idempotency semantics: pass2 must not introduce *additional* changes.
pass2_diff="$(git diff)"
pass2_diff_cached="$(git diff --cached)"

if [[ "${pass2_diff}" != "${pass1_diff}" ]] || [[ "${pass2_diff_cached}" != "${pass1_diff_cached}" ]]; then
  echo
  echo "==> status after pass2:"
  git status --porcelain >&2
  die "idempotency failure: pass2 changed the diff state vs pass1"
  fi
fi
echo "==> idempotency OK (pass2 introduced no new changes)"

if [[ "${commit_enabled}" == "1" ]]; then
  if [[ "${pass1_changed}" != "1" ]]; then
    echo "OK: --commit requested but no changes occurred (no-op); skipping commit"
  else
    echo
    echo "=== Commit (explicit) ==="
    git add -A
    if git diff --cached --quiet; then
      die "unexpected: nothing staged after git add -A"
    fi
    git commit -m "${commit_msg}"

    if [[ -n "$(git status --porcelain)" ]]; then
      die "post-commit tree not clean (unexpected)"
    fi
  fi
fi

  echo "=== Prove: scripts/prove_ci.sh ==="
  ./scripts/prove_ci.sh
else
  if [[ -n "$(git status --porcelain)" ]]; then
    die "tree not clean after successful run; use --commit or revert changes"
  fi

  echo
  echo "=== Prove: scripts/prove_ci.sh ==="
  ./scripts/prove_ci.sh
fi

echo
echo "=== Ops Orchestrator: OK ==="
