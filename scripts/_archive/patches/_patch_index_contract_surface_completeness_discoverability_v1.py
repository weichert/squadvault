from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CONTRACT_SURFACE_COMPLETENESS_INDEX_v1_BEGIN -->"
END = "<!-- SV_CONTRACT_SURFACE_COMPLETENESS_INDEX_v1_END -->"

BLOCK = f"""\
{BEGIN}
- scripts/gate_contract_surface_completeness_v1.sh — Enforce contract surface completeness (v1)
- scripts/prove_contract_surface_completeness_v1.sh — Proof: contract surface completeness gate (v1)
{END}
"""


def main() -> None:
  if not DOC.exists():
    raise SystemExit(f"ERROR: missing {DOC}")

  s = DOC.read_text(encoding="utf-8")

  if BEGIN in s and END in s:
    pre, mid = s.split(BEGIN, 1)
    inside, post = mid.split(END, 1)
    current = f"{BEGIN}{inside}{END}"
    expected_inner = BLOCK.split(BEGIN, 1)[1].split(END, 1)[0]
    expected = f"{BEGIN}\n{expected_inner}{END}"
    if current != expected:
      raise SystemExit("ERROR: existing bounded block mismatch (refuse).")
    return

  anchor = "gate_contract_linkage_v1.sh"
  if anchor in s:
    lines = s.splitlines(True)
    out: list[str] = []
    inserted = False
    for line in lines:
      out.append(line)
      if (not inserted) and (anchor in line):
        out.append(BLOCK)
        inserted = True
    if not inserted:
      raise SystemExit("ERROR: failed to insert bounded block (line scan).")
    DOC.write_text("".join(out), encoding="utf-8")
    return

  if not s.endswith("\n"):
    s += "\n"
  s += "\n" + BLOCK
  DOC.write_text(s, encoding="utf-8")


if __name__ == "__main__":
  main()
