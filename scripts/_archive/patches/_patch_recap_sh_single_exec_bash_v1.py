#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("scripts/recap.sh")
s0 = p.read_text(encoding="utf-8")

# Refuse if it doesn't look like the known shim.
if "SquadVault — recap CLI shim" not in s0 or "scripts/recap.py" not in s0:
    raise SystemExit("ERROR: recap.sh does not look like expected shim. Refusing to patch.")

# Build canonical content (small, deterministic).
canonical = """#!/usr/bin/env bash
# SquadVault — recap CLI shim (deterministic python path)
# Purpose: run the canonical scripts/recap.py via scripts/py to enforce repo imports.
# CWD-independent: resolves paths relative to this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec "${SCRIPT_DIR}/py" "${REPO_ROOT}/scripts/recap.py" "$@"
"""

# Idempotency: if already exactly canonical, do nothing.
if s0 == canonical:
    print("OK: recap.sh already canonical; no changes.")
    raise SystemExit(0)

# Refuse if file has unexpected constructs that suggest manual edits we might clobber.
# (We intentionally overwrite to canonical, but only if it includes the old ROOT+exec pattern.)
if 'exec "$ROOT/scripts/py" "$ROOT/scripts/recap.py" "$@"' not in s0 and 'exec "${SCRIPT_DIR}/py" "${REPO_ROOT}/scripts/recap.py" "$@"' not in s0:
    raise SystemExit("ERROR: recap.sh missing expected exec pattern. Refusing to overwrite.")

p.write_text(canonical, encoding="utf-8")
print("OK: rewrote recap.sh to single canonical bash exec (CWD-independent)")
