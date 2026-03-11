from __future__ import annotations

from pathlib import Path

PROVE_CI = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: contract_surface_completeness (v1) begin"
END = "# SV_GATE: contract_surface_completeness (v1) end"

BLOCK = f"""\
{BEGIN}
bash scripts/prove_contract_surface_completeness_v1.sh
{END}
"""


def main() -> None:
  if not PROVE_CI.exists():
    raise SystemExit(f"ERROR: missing {PROVE_CI}")

  s = PROVE_CI.read_text(encoding="utf-8")

  if BEGIN in s and END in s:
    pre, mid = s.split(BEGIN, 1)
    inside, post = mid.split(END, 1)
    current = f"{BEGIN}{inside}{END}"
    expected_inner = BLOCK.split(BEGIN, 1)[1].split(END, 1)[0]
    expected = f"{BEGIN}\n{expected_inner}{END}"
    if current != expected:
      raise SystemExit("ERROR: existing bounded block does not match expected (refuse).")
    return

  needle = "bash scripts/gate_contract_linkage_v1.sh"
  if needle not in s:
    raise SystemExit(f"ERROR: could not find insertion anchor in prove_ci.sh: {needle}")

  lines = s.splitlines(True)
  out: list[str] = []
  inserted = False

  for line in lines:
    out.append(line)
    if (not inserted) and (needle in line):
      out.append(BLOCK)
      inserted = True

  if not inserted:
    raise SystemExit("ERROR: failed to insert contract surface completeness block.")

  PROVE_CI.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
  main()
