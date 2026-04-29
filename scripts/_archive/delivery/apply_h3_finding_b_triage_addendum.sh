#!/usr/bin/env bash
# apply_h3_finding_b_triage_addendum.sh
#
# Apply the H3 amendment (closure addendum log) to the F-series
# Finding B triage memo. The amendment adds 160 lines documenting
# every closure (F1-F7, Findings B/C/D/E/F, H1+H4) plus the workstream
# summary table and the closure-verification lesson.
#
# This OVERWRITES the existing memo with the amended version. The
# amendment is append-only at the content level (only adds an addendum
# section after the existing 'Gates passed' section); the file is
# overwritten because that is how str_replace ships.

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
    echo "  applied: ${dest_rel}"
    echo "    from:  $(basename "${newest}")"
}

echo "Applying H3 (F-series triage memo addendum) to ${REPO_ROOT}..."
echo

apply_one "OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE*.md" \
          "_observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md"

echo
echo "Memo amended. Verify, then commit:"
echo "  # Confirm the diff is purely additive (~160 line addition):"
echo "  git diff --stat _observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md"
echo "  git diff _observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md | head -30"
echo
echo "  python3 -m pytest Tests/test_repo_root_allowlist_v1.py -q"
echo "  git add _observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md"
echo '  git commit -m "obs F-series triage memo: closure addendum log (H3)"'
echo "  git push origin main"
echo
echo "After successful merge:"
echo "  mv ~/Downloads/apply_h3_finding_b_triage_addendum*.sh scripts/_archive/delivery/"
