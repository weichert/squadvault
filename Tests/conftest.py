"""Pytest bootstrap for local imports.

Goal:
- Allow `pytest` to run without requiring callers to export PYTHONPATH.
- Ensure repo-root imports (e.g., `import scripts.recap`) and src-layout imports
  (e.g., `from squadvault...`) work deterministically.

This is test-only. It does not affect runtime packaging.
"""

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
