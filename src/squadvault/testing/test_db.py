"""SquadVault testing helpers (canonical).

Centralizes resolution of the canonical test DB path.

Hard invariant:
- Tests must not hardcode ".local_squadvault.sqlite" except via:
  os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")
  or resolve_test_db().
"""

from __future__ import annotations

import os


def resolve_test_db(default: str = ".local_squadvault.sqlite") -> str:
    v = os.environ.get("SQUADVAULT_TEST_DB")
    if v:
        return v
    return default
