from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

OLD_DIRS = r"grep -q 'dirs\.sort[[:space:]]*()'"
NEW_DIRS = r"grep -q '\(dirs\|dirnames\)\.sort[[:space:]]*()'  # accept_dirnames_filenames_sorts_v3"

OLD_FILES = r"grep -q 'files\.sort[[:space:]]*()'"
NEW_FILES = r"grep -q '\(files\|filenames\)\.sort[[:space:]]*()'  # accept_dirnames_filenames_sorts_v3"

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if "accept_dirnames_filenames_sorts_v3" in s:
        print("NO-OP: already patched (accept_dirnames_filenames_sorts_v3)")
        return

    if OLD_DIRS not in s:
        raise SystemExit(f"FAIL: could not find expected dirs grep pattern:\n{OLD_DIRS}")
    if OLD_FILES not in s:
        raise SystemExit(f"FAIL: could not find expected files grep pattern:\n{OLD_FILES}")

    s = s.replace(OLD_DIRS, NEW_DIRS, 1)
    s = s.replace(OLD_FILES, NEW_FILES, 1)

    TARGET.write_text(s, encoding="utf-8", newline="\n")
    print("OK: patched fs ordering gate to accept dirnames/filenames sorts (v3)")

if __name__ == "__main__":
    main()
