from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "prove_ci.sh"

MOVE_LINE = 'bash scripts/gate_repo_clean_after_proofs_v1.sh\n'
ANCHOR = 'bash scripts/gate_rivalry_chronicle_contract_linkage_v1.sh\n'

def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"ERROR: missing {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")

  if MOVE_LINE not in txt:
    raise SystemExit("ERROR: move line not found; refusing to patch.")
  if ANCHOR not in txt:
    raise SystemExit("ERROR: anchor line not found; refusing to patch.")

  desired = MOVE_LINE + ANCHOR
  if desired in txt:
    print("OK: gate_repo_clean_after_proofs already in canonical order (noop)")
    return

  # Remove all existing occurrences, then reinsert once at canonical anchor.
  txt2 = txt.replace(MOVE_LINE, "")
  txt2 = txt2.replace(ANCHOR, MOVE_LINE + ANCHOR, 1)

  TARGET.write_text(txt2, encoding="utf-8")
  print("OK: moved gate_repo_clean_after_proofs to canonical order (v1)")

if __name__ == "__main__":
  main()
