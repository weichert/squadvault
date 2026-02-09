from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CONTRACT_SURFACE_COMPLETENESS_v1_BEGIN -->"
END = "<!-- SV_CONTRACT_SURFACE_COMPLETENESS_v1_END -->"

PROOF_LINE = "- scripts/prove_contract_surface_completeness_v1.sh — Proof: contract surface completeness gate (v1)\n"
TARGET_PATH = "scripts/prove_contract_surface_completeness_v1.sh"

HEADER = "## Proof Runners (invoked by scripts/prove_ci.sh)"


def refuse(msg: str) -> None:
  raise SystemExit(f"ERROR: {msg}")


def remove_bounded_block(s: str) -> str:
  if BEGIN not in s and END not in s:
    return s
  if BEGIN not in s or END not in s:
    refuse("contract-surface bounded block markers are unpaired in registry (refuse)")
  pre, mid = s.split(BEGIN, 1)
  inside, post = mid.split(END, 1)
  return pre.rstrip("\n") + "\n" + post.lstrip("\n")


def remove_all_exact_line_occurrences(s: str, needle: str) -> str:
  want = needle.rstrip("\n")
  out_lines: list[str] = []
  for ln in s.splitlines(True):
    if ln.rstrip("\n") == want:
      continue
    out_lines.append(ln)
  return "".join(out_lines)


def find_header_index(lines: list[str]) -> int:
  idxs = [i for i, ln in enumerate(lines) if ln.rstrip("\n") == HEADER]
  if len(idxs) != 1:
    refuse(f"expected exactly one header line '{HEADER}' in registry; found {len(idxs)}")
  return idxs[0]


def find_first_prove_bullet_after(lines: list[str], start_idx: int) -> int:
  for i in range(start_idx + 1, len(lines)):
    ln = lines[i]
    if ln.startswith("## "):
      break
    if ln.startswith("- scripts/prove_"):
      return i
  refuse("could not find any '- scripts/prove_' bullet under Proof Runners header (unexpected registry shape)")
  return -1


def find_bullet_block(lines: list[str], first_bullet_idx: int) -> tuple[int, int]:
  """
  Returns (start, end) of the contiguous bullet block beginning at first_bullet_idx.
  Stops at:
    - next '## ' header, OR
    - first non-bullet line after bullets have started (blank line ends the block too).
  """
  start = first_bullet_idx
  j = start
  while j < len(lines):
    ln = lines[j]
    if ln.startswith("## "):
      break
    if ln.strip() == "":
      break
    if not ln.startswith("- "):
      break
    j += 1
  end = j
  return start, end


def extract_script_path_from_bullet(ln: str) -> str | None:
  if not ln.startswith("- "):
    return None
  body = ln[2:].strip()
  if not body.startswith("scripts/"):
    return None
  parts = body.split()
  if not parts:
    return None
  p = parts[0]
  if not p.endswith(".sh"):
    return None
  return p


def main() -> None:
  if not DOC.exists():
    refuse(f"missing {DOC}")

  s = DOC.read_text(encoding="utf-8")

  # Remove old bounded block + remove duplicates anywhere
  s = remove_bounded_block(s)
  s = remove_all_exact_line_occurrences(s, PROOF_LINE)

  lines = s.splitlines(True)

  header_idx = find_header_index(lines)
  first_bullet_idx = find_first_prove_bullet_after(lines, header_idx)
  start, end = find_bullet_block(lines, first_bullet_idx)

  block = lines[start:end]

  # If already in Proof Runners block (shouldn't happen after removal), no-op
  for ln in block:
    if ln.rstrip("\n") == PROOF_LINE.rstrip("\n"):
      DOC.write_text("".join(lines), encoding="utf-8")
      return

  # Determine lexicographic insertion point among scripts/prove_* paths
  insert_rel = None
  for i, ln in enumerate(block):
    p = extract_script_path_from_bullet(ln)
    if p is None:
      continue
    if not p.startswith("scripts/prove_"):
      continue
    if TARGET_PATH < p:
      insert_rel = i
      break

  if insert_rel is None:
    insert_rel = len(block)

  new_block = block[:insert_rel] + [PROOF_LINE] + block[insert_rel:]

  out: list[str] = []
  out.extend(lines[:start])
  out.extend(new_block)
  out.extend(lines[end:])

  DOC.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
  main()
