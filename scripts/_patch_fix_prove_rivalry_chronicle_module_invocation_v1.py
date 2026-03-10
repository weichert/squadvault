from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "prove_rivalry_chronicle_end_to_end_v1.sh"

OLD_GEN = """./scripts/py -u src/squadvault/consumers/rivalry_chronicle_generate_v1.py \\
"""
NEW_GEN = """PYTHONPATH=src ./scripts/py -u -m squadvault.consumers.rivalry_chronicle_generate_v1 \\
"""

OLD_APPROVE = """./scripts/py -u src/squadvault/consumers/rivalry_chronicle_approve_v1.py \\
"""
NEW_APPROVE = """PYTHONPATH=src ./scripts/py -u -m squadvault.consumers.rivalry_chronicle_approve_v1 \\
"""

def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"ERROR: missing {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")
  txt2 = txt

  if NEW_GEN not in txt2:
    if OLD_GEN not in txt2:
      raise SystemExit("ERROR: generate invocation anchor not found; refusing to patch.")
    txt2 = txt2.replace(OLD_GEN, NEW_GEN, 1)

  if NEW_APPROVE not in txt2:
    if OLD_APPROVE not in txt2:
      raise SystemExit("ERROR: approve invocation anchor not found; refusing to patch.")
    txt2 = txt2.replace(OLD_APPROVE, NEW_APPROVE, 1)

  if txt2 == txt:
    print("OK: prove_rivalry_chronicle_end_to_end_v1 module invocation already canonical (noop)")
    return

  TARGET.write_text(txt2, encoding="utf-8")
  print("OK: patched Rivalry Chronicle proof to use module invocation (v1)")

if __name__ == "__main__":
  main()
