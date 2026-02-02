from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path("Tests")
NEEDLE = '".local_squadvault.sqlite"'
REPL = 'os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")'


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def ensure_import_os(py_text: str) -> str:
    lines = py_text.splitlines(keepends=True)

    for ln in lines:
        if ln.strip() == "import os" or ln.strip().startswith("import os,") or ln.strip().startswith("import os "):
            return py_text

    i = 0
    n = len(lines)

    if i < n and lines[i].startswith("#!"):
        i += 1
    if i < n and "coding" in lines[i] and lines[i].lstrip().startswith("#"):
        i += 1

    while i < n and (lines[i].strip() == "" or lines[i].lstrip().startswith("#")):
        i += 1

    if i < n and (lines[i].lstrip().startswith('"""') or lines[i].lstrip().startswith("'''")):
        quote = '"""' if lines[i].lstrip().startswith('"""') else "'''"
        i += 1
        while i < n and quote not in lines[i]:
            i += 1
        if i < n:
            i += 1
        while i < n and lines[i].strip() == "":
            i += 1

    out = lines[:i] + ["import os\n"] + lines[i:]
    return "".join(out)


def main() -> None:
    if not TESTS_DIR.exists():
        die(f"missing Tests/ directory at: {TESTS_DIR}")

    py_files = sorted([p for p in TESTS_DIR.rglob("*.py") if p.is_file()])
    if not py_files:
        die("no python files found under Tests/")

    touched: list[Path] = []
    found_any = False

    for p in py_files:
        s = p.read_text(encoding="utf-8")
        if NEEDLE not in s:
            continue

        found_any = True
        s2 = s.replace(NEEDLE, REPL)

        if "os.environ.get(" in s2:
            s2 = ensure_import_os(s2)

        if s2 == s:
            die(f"unexpected no-op after replacement in {p} (refusing)")

        p.write_text(s2, encoding="utf-8")
        touched.append(p)

    if not found_any:
        die('no occurrences of ".local_squadvault.sqlite" found under Tests/ (refusing to patch)')

    print("OK: patched Tests/ to use SQUADVAULT_TEST_DB env var")
    for p in touched:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
