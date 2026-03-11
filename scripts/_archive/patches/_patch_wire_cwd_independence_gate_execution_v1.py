from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/prove_ci.sh")

OLD = """echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
gate_path="${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"

# SV_GATE: proof_registry_excludes_gates (v1) begin
"""

NEW = """echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
gate_path="${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"
bash "$gate_path"

# SV_GATE: proof_registry_excludes_gates (v1) begin
"""

def fail(msg: str) -> None:
    print("ERROR: " + msg, file=sys.stderr)
    raise SystemExit(1)

text = TARGET.read_text(encoding="utf-8")

if OLD not in text:
    fail("expected CWD independence gate anchor block not found")

updated = text.replace(OLD, NEW, 1)

if updated == text:
    print("OK: no changes required")
    raise SystemExit(0)

TARGET.write_text(updated, encoding="utf-8")
print("OK: patched scripts/prove_ci.sh")
