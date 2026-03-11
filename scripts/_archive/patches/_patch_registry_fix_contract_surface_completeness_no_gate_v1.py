from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CONTRACT_SURFACE_COMPLETENESS_v1_BEGIN -->"
END = "<!-- SV_CONTRACT_SURFACE_COMPLETENESS_v1_END -->"

EXPECTED_BLOCK = f"""\
{BEGIN}
- scripts/prove_contract_surface_completeness_v1.sh — Proof: contract surface completeness gate (v1)
{END}
"""


def refuse(msg: str) -> None:
  raise SystemExit(f"ERROR: {msg}")


def main() -> None:
  if not DOC.exists():
    refuse(f"missing {DOC}")

  s = DOC.read_text(encoding="utf-8")

  if BEGIN not in s or END not in s:
    refuse("expected bounded block not found for contract surface completeness (v1)")

  pre, mid = s.split(BEGIN, 1)
  inside, post = mid.split(END, 1)

  current = f"{BEGIN}{inside}{END}"
  expected_inner = EXPECTED_BLOCK.split(BEGIN, 1)[1].split(END, 1)[0]
  expected = f"{BEGIN}\n{expected_inner}{END}"

  # normalize: allow extra trailing whitespace lines inside, but refuse any unexpected content
  cur_lines = [ln.rstrip() for ln in current.splitlines()]
  exp_lines = [ln.rstrip() for ln in expected.splitlines()]

  if cur_lines == exp_lines:
    return

  # If current contains the forbidden gate line, replace entire block with expected.
  if "gate_contract_surface_completeness_v1.sh" in current:
    new_s = pre + EXPECTED_BLOCK + post
    DOC.write_text(new_s, encoding="utf-8")
    return

  refuse("bounded block content mismatch and does not contain forbidden gate line (refuse)")


if __name__ == "__main__":
  main()
