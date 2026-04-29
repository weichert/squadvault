#!/usr/bin/env bash
# apply_h1_h4_prove_ci_and_status.sh
#
# Apply both H1 (Finding B mechanism closure: set -euo pipefail to
# scripts/prove_ci.sh) and H4 (retire dangling _status.sh source from
# scripts/recap) from ~/Downloads. Two-file delivery, single commit.
#
# These items are bundled because H1 (set -e) surfaced H4 (the dead
# source line) as the silent-rc=1 case it was designed to expose. The
# fix to ship H1 cleanly is to also remove the dead source line in
# the same commit.
#
# IMPORTANT: validation is non-trivial. Run prove_ci.sh AFTER apply
# AND after cleaning any untracked files in the working tree (the
# worktree-cleanliness gate counts untracked files as ERRORs).

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
    chmod +x "${dest_abs}" 2>/dev/null || true
    echo "  applied: ${dest_rel}"
    echo "    from:  $(basename "${newest}")"
}

echo "Applying H1+H4 (Finding B closure + _status.sh retirement) to ${REPO_ROOT}..."
echo

apply_one "prove_ci*.sh"   "scripts/prove_ci.sh"
apply_one "recap_script*"  "scripts/recap"

echo
echo "Both files applied. NOW VALIDATE BEFORE COMMITTING:"
echo
echo "  # 1. Confirm the diff is exactly the 8-line addition + 3-line removal:"
echo "  git diff --stat scripts/prove_ci.sh scripts/recap"
echo "  git diff scripts/prove_ci.sh"
echo "  git diff scripts/recap"
echo
echo "  # 2. The worktree-cleanliness gate counts untracked files as ERRORs."
echo "  #    Make sure any unrelated untracked files are dealt with first."
echo "  git status"
echo "  # If there are untracked items unrelated to this commit (like an"
echo "  # archived apply script from a prior session), either commit them"
echo "  # to scripts/_archive/delivery/ in a SEPARATE commit first, or"
echo "  # accept that the ERROR count from prove_ci.sh will reflect them."
echo
echo "  # 3. Run prove_ci.sh and capture rc and ERROR count:"
echo "  bash scripts/prove_ci.sh > /tmp/proveci_h1h4_post.txt 2>&1"
echo "  rc=\$?"
echo "  echo \"prove_ci rc=\$rc\""
echo "  grep -c -E '^ERROR|ERROR:' /tmp/proveci_h1h4_post.txt"
echo
echo "  # 4. Expected: rc=0."
echo "  #    ERROR count: 1 (env-only export-assemblies issue) IF worktree"
echo "  #    is fully clean. Higher counts likely reflect untracked files."
echo "  #    rc != 0: roll back BOTH files and triage. Do NOT commit."
echo
echo "  # 5. Confirm the original 'No such file or directory' line is GONE"
echo "  #    from prove_ci.sh output (the H4 evidence):"
echo "  grep -c '_status.sh: No such file' /tmp/proveci_h1h4_post.txt"
echo "  # Expected: 0"
echo
echo "If validation passes, commit:"
echo "  git add scripts/prove_ci.sh scripts/recap"
echo '  git commit -F "$(ls -t ~/Downloads/h1_h4_combined_commit_msg*.txt | head -1)"'
echo "  git push origin main"
echo
echo "If validation fails:"
echo "  git checkout -- scripts/prove_ci.sh scripts/recap   # discard both"
echo "  # Then capture the failure mode in an observation memo and triage."
echo
echo "After successful merge, archive this script:"
echo "  mv ~/Downloads/apply_h1_h4_prove_ci_and_status*.sh scripts/_archive/delivery/"
