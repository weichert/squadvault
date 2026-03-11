from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS_INIT = ROOT / "scripts" / "__init__.py"
CONFTEST = ROOT / "Tests" / "conftest.py"

CONFTEST_TEXT = """\
\"\"\"Pytest bootstrap for local imports.

Goal:
- Allow `pytest` to run without requiring callers to export PYTHONPATH.
- Ensure repo-root imports (e.g., `import scripts.recap`) and src-layout imports
  (e.g., `from squadvault...`) work deterministically.

This is test-only. It does not affect runtime packaging.
\"\"\"

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Ensure repo root is first (for `import scripts.*`)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure src layout is available (for `import squadvault.*`)
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
"""

def main() -> int:
    # 1) scripts becomes an importable package for tests
    SCRIPTS_INIT.parent.mkdir(parents=True, exist_ok=True)
    if not SCRIPTS_INIT.exists():
        SCRIPTS_INIT.write_text("# Package marker for tests (allows `import scripts.*`).\n", encoding="utf-8")
        print(f"created: {SCRIPTS_INIT.relative_to(ROOT)}")
    else:
        print(f"ok: exists: {SCRIPTS_INIT.relative_to(ROOT)}")

    # 2) pytest path bootstrap
    CONFTEST.parent.mkdir(parents=True, exist_ok=True)
    before = CONFTEST.read_text(encoding="utf-8") if CONFTEST.exists() else None
    CONFTEST.write_text(CONFTEST_TEXT, encoding="utf-8")
    changed = (before != CONFTEST_TEXT)
    print(f"wrote: {CONFTEST.relative_to(ROOT)}")
    print(f"changed: {changed}")

    print("Next:")
    print("  pytest -q")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
