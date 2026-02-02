from __future__ import annotations

import sys
from pathlib import Path


TESTS_DIR = Path("Tests")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TESTS_DIR.exists():
        die(f"missing Tests/ directory at: {TESTS_DIR}")

    py_files = sorted([p for p in TESTS_DIR.rglob("*.py") if p.is_file()])
    if not py_files:
        die("no python files found under Tests/")

    touched: list[Path] = []

    for p in py_files:
        s = p.read_text(encoding="utf-8")

        needle_a = "import os\nfrom __future__ import annotations\n"
        needle_b = "import os\n\nfrom __future__ import annotations\n"

        if needle_a not in s and needle_b not in s:
            continue

        if "from __future__ import annotations" not in s:
            die(f"unexpected: matched ordering needle but missing future import in {p}")

        if needle_a in s:
            s2 = s.replace(
                needle_a,
                "from __future__ import annotations\nimport os\n",
                1,
            )
        else:
            s2 = s.replace(
                needle_b,
                "from __future__ import annotations\n\nimport os\n",
                1,
            )

        if s2 == s:
            die(f"no-op after replacement in {p} (refusing)")

        p.write_text(s2, encoding="utf-8")
        touched.append(p)

    if not touched:
        die("no Tests/*.py files required future-import reorder fix (refusing)")

    print("OK: fixed future-import ordering (import os after __future__)")
    for p in touched:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
