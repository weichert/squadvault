from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if "accept_dirnames_filenames_sorts_v1" in s:
        print("NO-OP: already patched (accept_dirnames_filenames_sorts_v1)")
        return

    # Replace the two grep checks inside the os.walk window scan:
    #   grep -q 'dirs\.sort()'  -> accept dirs.sort() OR dirnames.sort()
    #   grep -q 'files\.sort()' -> accept files.sort() OR filenames.sort()
    #
    # Keep the "within next 5 lines" behavior unchanged.

    s2, n1 = re.subn(
        r"grep -q 'dirs\\\.sort\\[\\[:space:\\]\\]\\*\\(\\)'",
        r"grep -q '\(dirs\|dirnames\)\\.sort[[:space:]]*()'  # accept_dirnames_filenames_sorts_v1",
        s,
        count=1,
    )
    if n1 != 1:
        raise SystemExit("FAIL: could not patch dirs.sort() guard")

    s3, n2 = re.subn(
        r"grep -q 'files\\\.sort\\[\\[:space:\\]\\]\\*\\(\\)'",
        r"grep -q '\(files\|filenames\)\\.sort[[:space:]]*()'  # accept_dirnames_filenames_sorts_v1",
        s2,
        count=1,
    )
    if n2 != 1:
        raise SystemExit("FAIL: could not patch files.sort() guard")

    TARGET.write_text(s3, encoding="utf-8", newline="\n")
    print("OK: patched fs ordering gate to accept dirnames/filenames sorts (v1)")

if __name__ == "__main__":
    main()
