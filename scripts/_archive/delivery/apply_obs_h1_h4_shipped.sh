#!/usr/bin/env bash
# apply_obs_h1_h4_shipped.sh
#
# Apply the H1+H4 shipping observation memo to _observations/.
# Single-file delivery.

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

echo "Applying H1+H4 observation memo to ${REPO_ROOT}..."
echo

apply_one "OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED*.md" \
          "_observations/OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md"

echo
echo "Memo applied. Commit:"
echo "  python3 -m pytest Tests/test_repo_root_allowlist_v1.py -q"
echo "  git add _observations/OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md"
echo '  git commit -m "obs H1+H4 shipped, memory_events gate exposed"'
echo "  git push origin main"
echo
echo "After successful merge:"
echo "  mv ~/Downloads/apply_obs_h1_h4_shipped*.sh scripts/_archive/delivery/"
echo "  mv ~/Downloads/apply_h1_h4_prove_ci_and_status*.sh scripts/_archive/delivery/"
