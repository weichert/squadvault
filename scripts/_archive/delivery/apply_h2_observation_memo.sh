#!/usr/bin/env bash
# apply_h2_observation_memo.sh
#
# Apply ONLY the H2 observation memo to _observations/. The H2 fix
# itself is generated locally — see h2_runbook.md.

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

echo "Applying H2 observation memo to ${REPO_ROOT}..."
echo

apply_one "OBSERVATIONS_2026_04_29_H2_RUFF_AUTOFIX*.md" \
          "_observations/OBSERVATIONS_2026_04_29_H2_RUFF_AUTOFIX.md"

echo
echo "Memo applied. NOTE: this is the OBSERVATION memo only."
echo "The H2 ruff auto-fix itself is run locally per h2_runbook.md."
echo
echo "Recommended order:"
echo "  1. Run the auto-fix per h2_runbook.md."
echo "  2. After that commit lands, commit this observation memo."
echo
echo "  python3 -m pytest Tests/test_repo_root_allowlist_v1.py -q"
echo "  git add _observations/OBSERVATIONS_2026_04_29_H2_RUFF_AUTOFIX.md"
echo '  git commit -m "obs H2 ruff auto-fix shipped"'
echo "  git push origin main"
echo
echo "After successful merge:"
echo "  mv ~/Downloads/apply_h2_observation_memo*.sh scripts/_archive/delivery/"
