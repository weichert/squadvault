#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: fix runtime filesystem ordering (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python3}"
if ! command -v "${python}" >/dev/null 2>&1; then
  python="python"
fi

"${python}" - <<'PY'
from pathlib import Path
import re
import sys

REPO_ROOT = Path.cwd()

FILE1 = REPO_ROOT / "src/squadvault/consumers/editorial_review_week.py"
FILE2 = REPO_ROOT / "src/squadvault/validation/signals/signal_taxonomy_type_a_v1.py"

def patch_file1():
    txt = FILE1.read_text()
    old = 'for p in d.glob("recap_v*.json"):'
    new = 'for p in sorted(d.glob("recap_v*.json")):'
    if old in txt:
        FILE1.write_text(txt.replace(old, new, 1))
        print(f"OK: patched {FILE1}")
        return
    if new in txt:
        print(f"OK: already patched {FILE1}")
        return
    raise SystemExit(f"ERROR: expected line not found in {FILE1}: {old}")

def patch_file2():
    txt = FILE2.read_text()

    # Replace:
    #   for dirpath, _, files in os.walk(root):
    # with:
    #   for dirpath, dirs, files in os.walk(root):
    #       dirs.sort()
    #       files.sort()
    #
    # Keep indentation stable.
    pat = r'^(?P<indent>\s*)for dirpath, _?, files in os\.walk\(root\):\s*$'
    m = re.search(pat, txt, flags=re.MULTILINE)
    if not m:
        # already patched?
        if (
            "for dirpath, dirs, files in os.walk(root):" in txt
            and "dirs.sort()" in txt
            and "files.sort()" in txt
        ):
            print(f"OK: already patched {FILE2}")
            return
        raise SystemExit(f"ERROR: could not locate os.walk loop in {FILE2}")

    indent = m.group("indent")
    start, end = m.start(), m.end()

    replacement = "\n".join([
        f"{indent}for dirpath, dirs, files in os.walk(root):",
        f"{indent}    dirs.sort()",
        f"{indent}    files.sort()",
    ])

    txt2 = txt[:start] + replacement + txt[end:]
    FILE2.write_text(txt2)
    print(f"OK: patched {FILE2}")

def main():
    patch_file1()
    patch_file2()

if __name__ == "__main__":
    main()
PY

echo "==> py_compile"
python -m py_compile \
  src/squadvault/consumers/editorial_review_week.py \
  src/squadvault/validation/signals/signal_taxonomy_type_a_v1.py

echo "OK"
