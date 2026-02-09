from __future__ import annotations

from pathlib import Path
import sys


DOC = Path("docs/contracts/rivalry_chronicle_output_contract_v1.md")

HEADER = "## Enforced By"
EXPECTED_BULLETS = [
  "- `src/squadvault/consumers/rivalry_chronicle_generate_v1.py`",
  "- `src/squadvault/consumers/rivalry_chronicle_approve_v1.py`",
  "- `src/squadvault/chronicle/generate_rivalry_chronicle_v1.py`",
]


def die(msg: str) -> None:
  print(f"ERROR: {msg}", file=sys.stderr)
  raise SystemExit(2)


def find_section(lines: list[str]) -> tuple[int | None, int | None]:
  """
  Returns (start_idx, end_idx) inclusive for the Enforced By section.
  end_idx is the last line belonging to the section (before next heading).
  """
  start = None
  for i, line in enumerate(lines):
    if line.strip() == HEADER:
      start = i
      break
  if start is None:
    return (None, None)

  end = start
  for j in range(start + 1, len(lines)):
    if lines[j].startswith("## ") and j != start:
      end = j - 1
      break
    end = j
  return (start, end)


def normalize_block(block_lines: list[str]) -> list[str]:
  return [ln.rstrip() for ln in block_lines]


def expected_block() -> list[str]:
  out = [HEADER, ""]
  out.extend(EXPECTED_BULLETS)
  out.append("")
  return out


def insert_position(lines: list[str]) -> int:
  """
  Insert after the first H1 block if present, else at top.
  """
  if not lines:
    return 0

  h1 = None
  for i, ln in enumerate(lines):
    if ln.startswith("# "):
      h1 = i
      break
  if h1 is None:
    return 0

  for j in range(h1 + 1, len(lines)):
    if lines[j].strip() == "":
      return j + 1
  return len(lines)


def main() -> None:
  if not DOC.exists():
    die(f"missing contract doc: {DOC}")

  raw = DOC.read_text(encoding="utf-8")
  lines = raw.splitlines()

  start, end = find_section(lines)
  exp = expected_block()

  if start is None:
    pos = insert_position(lines)
    new_lines = lines[:pos] + exp + lines[pos:]
    DOC.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    print(f"OK: inserted Enforced By section into {DOC}")
    return

  existing = normalize_block(lines[start : end + 1])
  while existing and existing[-1] == "":
    existing.pop()

  exp_norm = normalize_block(exp)
  while exp_norm and exp_norm[-1] == "":
    exp_norm.pop()

  if existing != exp_norm:
    die(f"{DOC}: existing Enforced By section does not match expected surfaces; refuse")

  print(f"OK: already compliant: {DOC}")


if __name__ == "__main__":
  main()
