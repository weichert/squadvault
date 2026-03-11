from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    if not TARGET.exists():
        die(f"FAIL: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    # Patch 1: accept (dirs|dirnames).sort() and (files|filenames).sort()
    old1 = r"grep -q 'dirs\.sort[[:space:]]*()'"
    old2 = r"grep -q 'files\.sort[[:space:]]*()'"

    new1 = r"grep -Eq '(dirs|dirnames)\.sort[[:space:]]*\(\)'"
    new2 = r"grep -Eq '(files|filenames)\.sort[[:space:]]*\(\)'"

    if old1 not in s or old2 not in s:
        die("FAIL: did not find expected dirs.sort()/files.sort() checks (refuse to patch)")

    s2 = s.replace(old1, new1, 1).replace(old2, new2, 1)

    TARGET.write_text(s2, encoding="utf-8", newline="\n")
    print("PATCH_APPLIED: fs ordering gate accepts dirnames/filenames sorts (v1)")

if __name__ == "__main__":
    main()
