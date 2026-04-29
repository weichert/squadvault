#!/usr/bin/env bash
# apply_priority_list_2026_04_28.sh
#
# Apply the priority list re-grounding memo from ~/Downloads to its
# target path. Single-file delivery. Run from the repo root.
#
# This memo passes the repo-root allowlist gate
# (Tests/test_repo_root_allowlist_v1.py) because it lives under
# _observations/, which is in ALLOWED_ROOT_DIRS.
#
# After successful apply:
#
#   git status
#   git diff --stat
#
#   python3 -m pytest Tests/test_repo_root_allowlist_v1.py -q
#
#   git add _observations/PRIORITY_LIST_2026_04_28.md
#   git commit -F "$(ls -t ~/Downloads/priority_list_commit_msg*.txt | head -1)"
#   git push origin main

set -euo pipefail

DOWNLOADS="${HOME}/Downloads"
REPO_ROOT="$(pwd)"

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
    echo "ERROR: not in a git repository (no .git directory at ${REPO_ROOT})." >&2
    echo "       Run this script from the squadvault repo root." >&2
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
        echo "       Did you download the file? Check ${DOWNLOADS}/." >&2
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
        echo "       Are you running from the repo root?" >&2
        exit 1
    fi

    cp "${newest}" "${dest_abs}"
    echo "  applied: ${dest_rel}"
    echo "    from:  $(basename "${newest}")"
}

echo "Applying priority list memo to ${REPO_ROOT}..."
echo

apply_one "PRIORITY_LIST_2026_04_28*.md" \
          "_observations/PRIORITY_LIST_2026_04_28.md"

echo
echo "Memo applied."
echo
echo "Verify, then commit:"
echo "  git status"
echo "  python3 -m pytest Tests/test_repo_root_allowlist_v1.py -q"
echo "  git add _observations/PRIORITY_LIST_2026_04_28.md"
echo '  git commit -F "$(ls -t ~/Downloads/priority_list_commit_msg*.txt | head -1)"'
echo "  git push origin main"
echo
echo "After successful merge, archive this script:"
echo "  mv ~/Downloads/apply_priority_list_2026_04_28*.sh scripts/_archive/delivery/"
