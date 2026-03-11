from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

OLD_DIRS_LINE = r"echo ""${window}"" | grep -q 'dirs\.sort[[:space:]]*()' || { py_hits_oswalk_unsorted=""${py_hits_oswalk_unsorted}${hit}\n""; continue; }"
OLD_FILES_LINE = r"echo ""${window}"" | grep -q 'files\.sort[[:space:]]*()' || { py_hits_oswalk_unsorted=""${py_hits_oswalk_unsorted}${hit}\n""; continue; }"

# We will replace only the grep -q pattern portion (more robust than full-line replace).
OLD_DIRS_PAT = r"grep -q 'dirs\.sort[[:space:]]*()'"
NEW_DIRS_PAT = r"grep -q '\(dirs\|dirnames\)\.sort[[:space:]]*()'  # accept_dirnames_filenames_sorts_v2"

OLD_FILES_PAT = r"grep -q 'files\.sort[[:space:]]*()'"
NEW_FILES_PAT = r"grep -q '\(files\|filenames\)\.sort[[:space:]]*()'  # accept_dirnames_filenames_sorts_v2"

LN_ASSIGN = r'ln="$(printf "%s" "${hit}" | cut -d: -f2)"'
GUARD_MARK = "oswalk_numeric_guard_v2"

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if "accept_dirnames_filenames_sorts_v2" in s and GUARD_MARK in s:
        print("NO-OP: already patched (accept_dirnames_filenames_sorts_v2 + oswalk_numeric_guard_v2)")
        return

    # 1) Accept dirnames/filenames sorts
    if OLD_DIRS_PAT not in s:
        raise SystemExit(f"FAIL: could not find expected dirs grep pattern:\n{OLD_DIRS_PAT}")
    if OLD_FILES_PAT not in s:
        raise SystemExit(f"FAIL: could not find expected files grep pattern:\n{OLD_FILES_PAT}")

    s = s.replace(OLD_DIRS_PAT, NEW_DIRS_PAT, 1)
    s = s.replace(OLD_FILES_PAT, NEW_FILES_PAT, 1)

    # 2) Ensure ln numeric guard exists immediately after ln= assignment in os.walk loop
    if LN_ASSIGN not in s:
        raise SystemExit(f"FAIL: could not find ln= assignment line:\n{LN_ASSIGN}")

    if GUARD_MARK not in s:
        guard = (
            f'{LN_ASSIGN}\n'
            f'    # {GUARD_MARK}: defensive; ignore non-numeric line fields\n'
            f'    printf "%s" "${{ln}}" | grep -E -q \'^[0-9]+$\' || continue\n'
        )
        s = s.replace(LN_ASSIGN, guard, 1)

    TARGET.write_text(s, encoding="utf-8", newline="\n")
    print("OK: patched fs ordering gate to accept dirnames/filenames + enforced numeric ln guard (v2)")

if __name__ == "__main__":
    main()
