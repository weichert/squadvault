#!/usr/bin/env bash
# apply_h7a_memory_events_allowlist.sh
#
# Apply H7 Category A: update the memory_events gate allowlist for the
# run_ingest_then_canonicalize.py file move (core/canonicalize/ -> ops/).
# Single-line change in scripts/check_no_memory_reads.sh.

set -euo pipefail

DOWNLOADS="${HOME}/Downloads"
REPO_ROOT="$(pwd)"

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
    echo "ERROR: not in a git repository (no .git directory at ${REPO_ROOT})." >&2
    exit 1
fi

apply_one() {
    local pattern="$1"
    local dest_rel="$2"
    local dest_abs="${REPO_ROOT}/${dest_rel}"
    local dest_dir
    dest_dir="$(dirname "${dest_abs}")"

    local matches=( ${DOWNLOADS}/${pattern} )
    if [[ ! -e "${matches[0]}" ]]; then
        echo "ERROR: no source file matching '${pattern}' in ${DOWNLOADS}" >&2
        exit 1
    fi

    local newest
    newest="$(ls -t ${DOWNLOADS}/${pattern} | head -1)"
    if [[ ! -f "${newest}" ]]; then
        echo "ERROR: '${newest}' is not a regular file." >&2
        exit 1
    fi

    if [[ ! -d "${dest_dir}" ]]; then
        echo "ERROR: target directory does not exist: ${dest_dir}" >&2
        exit 1
    fi

    cp "${newest}" "${dest_abs}"
    chmod +x "${dest_abs}" 2>/dev/null || true
    echo "  applied: ${dest_rel}"
    echo "    from:  $(basename "${newest}")"
}

echo "Applying H7 Cat A (memory_events allowlist update) to ${REPO_ROOT}..."
echo

apply_one "check_no_memory_reads*.sh" "scripts/check_no_memory_reads.sh"

echo
echo "File applied. NOW VALIDATE BEFORE COMMITTING:"
echo
echo "  # 1. Confirm the diff is exactly the 1-line allowlist change:"
echo "  git diff scripts/check_no_memory_reads.sh"
echo
echo "  # 2. Run the gate; expect 4 violations remaining (down from 6),"
echo "  #    rc=1 (Cat B still open):"
echo "  bash scripts/check_no_memory_reads.sh"
echo
echo "  # 3. Confirm ops/run_ingest_then_canonicalize.py is no longer flagged:"
echo "  bash scripts/check_no_memory_reads.sh 2>&1 | grep -c run_ingest_then_canonicalize"
echo "  # Expected: 0"
echo
echo "If validation passes, commit:"
echo "  git add scripts/check_no_memory_reads.sh"
echo '  git commit -F "$(ls -t ~/Downloads/h7a_memory_events_allowlist_commit_msg*.txt | head -1)"'
echo "  git push origin main"
echo
echo "After successful merge:"
echo "  mv ~/Downloads/apply_h7a_memory_events_allowlist*.sh scripts/_archive/delivery/"
