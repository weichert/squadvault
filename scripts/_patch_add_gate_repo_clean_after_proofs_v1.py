from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROVE = REPO / "scripts" / "prove_ci.sh"
GATE = REPO / "scripts" / "gate_repo_clean_after_proofs_v1.sh"

MARKER = "REPO_CLEAN_AFTER_PROOFS_V1"

INSERT_BLOCK = (
  'echo "=== Gate: Enforce repo clean after proofs (v1) ==="\n'
  "bash scripts/gate_repo_clean_after_proofs_v1.sh\n"
)

ANCHOR_LINE = 'bash scripts/gate_worktree_cleanliness_v1.sh end "${SV_WORKTREE_SNAP0}"\n'

GATE_BODY = """#!/usr/bin/env bash
set -euo pipefail

# REPO_CLEAN_AFTER_PROOFS_V1
# Enforce: repo must be clean at end of CI proofs.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"

cd "${repo_root}"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git not found; cannot check repo cleanliness" >&2
  exit 2
fi

dirty="$(git status --porcelain=v1 2>/dev/null || true)"
if [[ -n "${dirty}" ]]; then
  echo "ERROR: repo not clean after proofs" >&2
  echo "${dirty}" >&2
  exit 2
fi

echo "OK: repo clean after proofs."
"""

def _read(p: Path) -> str:
  return p.read_text(encoding="utf-8")

def _write_if_changed(p: Path, s: str) -> bool:
  old = p.read_text(encoding="utf-8") if p.exists() else ""
  if old == s:
    return False
  p.parent.mkdir(parents=True, exist_ok=True)
  p.write_text(s, encoding="utf-8")
  return True

def main() -> None:
  if not PROVE.exists():
    raise SystemExit(f"ERROR: missing {PROVE}")

  changed = False

  # 1) Gate script
  changed |= _write_if_changed(GATE, GATE_BODY)

  # 2) prove_ci wiring (insert immediately before worktree_cleanliness end)
  prove_txt = _read(PROVE)
  if INSERT_BLOCK in prove_txt:
    pass
  else:
    if ANCHOR_LINE not in prove_txt:
      raise SystemExit(
        "ERROR: expected anchor line not found in scripts/prove_ci.sh:\n"
        f"  {ANCHOR_LINE.strip()}\n"
        "Refusing to patch."
      )
    prove_txt = prove_txt.replace(ANCHOR_LINE, INSERT_BLOCK + "\n" + ANCHOR_LINE, 1)
    PROVE.write_text(prove_txt, encoding="utf-8")
    changed = True

  # 3) +x (best effort)
  if GATE.exists():
    mode = GATE.stat().st_mode
    if (mode & 0o100) == 0:
      GATE.chmod(mode | 0o100)
      changed = True

  if changed:
    print("OK: applied patch_add_gate_repo_clean_after_proofs_v1 (v1)")
  else:
    print("OK: patch_add_gate_repo_clean_after_proofs_v1 already canonical (noop)")

if __name__ == "__main__":
  main()
