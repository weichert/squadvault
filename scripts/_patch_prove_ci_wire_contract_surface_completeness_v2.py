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


def refuse(msg: str) -> None:
  raise SystemExit(f"ERROR: {msg}")


def already_present(s: str) -> bool:
  return (BEGIN in s) and (END in s)


def ensure_idempotent_block(s: str) -> None:
  pre, mid = s.split(BEGIN, 1)
  inside, post = mid.split(END, 1)
  current = f"{BEGIN}{inside}{END}"
  expected_inner = BLOCK.split(BEGIN, 1)[1].split(END, 1)[0]
  expected = f"{BEGIN}\n{expected_inner}{END}"
  if current != expected:
    refuse("existing bounded block does not match expected (refuse)")


def find_anchor_index(lines: list[str]) -> int:
  """
  Deterministic anchor selection, in priority order:
  1) First line containing 'gate_contract_linkage_v1.sh'
  2) First line containing 'contracts_index' (discoverability / linkage cluster)
  3) First line containing 'gate_contracts' and '.sh'
  4) Line that starts the unit tests block: insert immediately before it.
  Refuse if none found.
  """
  # 1) direct linkage gate mention
  idxs = [i for i, ln in enumerate(lines) if "gate_contract_linkage_v1.sh" in ln]
  if len(idxs) > 1:
    refuse("multiple 'gate_contract_linkage_v1.sh' occurrences; ambiguous anchor")
  if len(idxs) == 1:
    return idxs[0] + 1

  # 2) contract index / discoverability mention
  idxs = [i for i, ln in enumerate(lines) if "contracts_index" in ln and ".sh" in ln]
  if len(idxs) > 1:
    refuse("multiple 'contracts_index' script occurrences; ambiguous anchor")
  if len(idxs) == 1:
    return idxs[0] + 1

  # 3) any gate_contracts*.sh
  idxs = [i for i, ln in enumerate(lines) if "gate_contract" in ln and ".sh" in ln]
  if len(idxs) > 1:
    # deterministic choice: insert after the *last* contract-related gate line
    return idxs[-1] + 1
  if len(idxs) == 1:
    return idxs[0] + 1

  # 4) before unit tests header (stable section boundary)
  idxs = [i for i, ln in enumerate(lines) if "==> unit tests" in ln]
  if len(idxs) > 1:
    refuse("multiple unit test section markers; unexpected prove_ci shape")
  if len(idxs) == 1:
    return idxs[0]

  refuse("could not find any deterministic insertion anchor in scripts/prove_ci.sh")
  return -1


def main() -> None:
  if not PROVE_CI.exists():
    refuse(f"missing {PROVE_CI}")

  s = PROVE_CI.read_text(encoding="utf-8")

  if already_present(s):
    ensure_idempotent_block(s)
    return

  lines = s.splitlines(True)
  insert_at = find_anchor_index(lines)

  out: list[str] = []
  out.extend(lines[:insert_at])

  # Ensure exactly one blank line before insertion if needed
  if out and out[-1].strip() != "":
    out.append("\n")

  out.append(BLOCK)

  # Ensure exactly one blank line after insertion if next line isn't blank
  if insert_at < len(lines) and (lines[insert_at].strip() != ""):
    out.append("\n")

  out.extend(lines[insert_at:])

  PROVE_CI.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
  main()
