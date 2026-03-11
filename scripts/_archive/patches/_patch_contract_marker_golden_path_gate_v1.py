from __future__ import annotations

from pathlib import Path
import sys


TARGET = Path("scripts/gate_golden_path_output_contract_v1.sh")

# Normalize from older/non-versioned name to versioned contract name.
NAME_EXPECTED = "# SV_CONTRACT_NAME: GOLDEN_PATH_OUTPUT_CONTRACT_V1"
DOC_EXPECTED = "# SV_CONTRACT_DOC_PATH: docs/contracts/golden_path_output_contract_v1.md"

NAME_PREFIX = "# SV_CONTRACT_NAME:"
DOC_PREFIX = "# SV_CONTRACT_DOC_PATH:"


def die(msg: str) -> None:
  print(f"ERROR: {msg}", file=sys.stderr)
  raise SystemExit(2)


def is_shebang(line: str) -> bool:
  return line.startswith("#!")


def is_blank(line: str) -> bool:
  return line.strip() == ""


def is_comment(line: str) -> bool:
  return line.lstrip().startswith("#")


def first_executable_line_idx(lines: list[str]) -> int:
  """
  Find first line that is not blank/comment.
  In bash scripts, 'set -euo pipefail' counts as executable.
  """
  for i, ln in enumerate(lines):
    if is_blank(ln) or is_comment(ln):
      continue
    return i
  return len(lines)


def find_marker_indices(lines: list[str]) -> tuple[int | None, int | None]:
  name_idx = None
  doc_idx = None
  for i, ln in enumerate(lines):
    if ln.strip().startswith(NAME_PREFIX):
      if name_idx is not None:
        die(f"{TARGET}: multiple SV_CONTRACT_NAME lines found; refuse")
      name_idx = i
    if ln.strip().startswith(DOC_PREFIX):
      if doc_idx is not None:
        die(f"{TARGET}: multiple SV_CONTRACT_DOC_PATH lines found; refuse")
      doc_idx = i

  if (name_idx is None) ^ (doc_idx is None):
    die(f"{TARGET}: partial contract marker present (one of two lines missing)")

  return (name_idx, doc_idx)


def ensure_markers_normalized() -> None:
  if not TARGET.exists():
    die(f"missing target file: {TARGET}")

  raw = TARGET.read_text(encoding="utf-8")
  lines_ke = raw.splitlines(True)
  lines = [l.rstrip("\n") for l in lines_ke]

  name_idx, doc_idx = find_marker_indices(lines)

  # If markers exist, enforce they are in header (before first executable code).
  exec_idx = first_executable_line_idx(lines)
  if name_idx is not None and name_idx >= exec_idx:
    die(f"{TARGET}: contract markers appear after executable code; refuse")

  # If absent entirely, insert after shebang (or at top) in canonical header position.
  if name_idx is None:
    insert_at = 1 if (len(lines) > 0 and is_shebang(lines[0])) else 0
    # If shebang exists and there is an immediate blank line, keep spacing canonical:
    block = [NAME_EXPECTED + "\n", DOC_EXPECTED + "\n", "\n"]
    new_lines = lines_ke[:insert_at] + block + lines_ke[insert_at:]
    TARGET.write_text("".join(new_lines), encoding="utf-8")
    return

  # If present: rewrite to exact expected lines, preserving surrounding newlines.
  changed = False

  if lines_ke[name_idx].rstrip("\n") != NAME_EXPECTED:
    lines_ke[name_idx] = NAME_EXPECTED + "\n"
    changed = True

  if lines_ke[doc_idx].rstrip("\n") != DOC_EXPECTED:
    lines_ke[doc_idx] = DOC_EXPECTED + "\n"
    changed = True

  if changed:
    TARGET.write_text("".join(lines_ke), encoding="utf-8")


def main() -> None:
  before = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
  ensure_markers_normalized()
  after = TARGET.read_text(encoding="utf-8")
  if before != after:
    print(f"OK: normalized contract markers in {TARGET}")
  else:
    print(f"OK: already compliant: {TARGET}")


if __name__ == "__main__":
  main()
