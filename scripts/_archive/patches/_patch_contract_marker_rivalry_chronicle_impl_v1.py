from __future__ import annotations

from pathlib import Path
import sys


TARGET = Path("src/squadvault/chronicle/generate_rivalry_chronicle_v1.py")

NAME_LINE = "# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT_CONTRACT_V1"
DOC_LINE = "# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md"


def die(msg: str) -> None:
  print(f"ERROR: {msg}", file=sys.stderr)
  raise SystemExit(2)


def is_shebang(line: str) -> bool:
  return line.startswith("#!")


def is_encoding(line: str) -> bool:
  s = line.strip()
  return s.startswith("#") and ("coding" in s) and ("utf" in s)


def is_comment(line: str) -> bool:
  return line.lstrip().startswith("#")


def is_blank(line: str) -> bool:
  return line.strip() == ""


def is_import(line: str) -> bool:
  s = line.lstrip()
  return s.startswith("import ") or s.startswith("from ")


def parse_top_module_docstring(lines: list[str], start_idx: int) -> tuple[int | None, int | None]:
  """
  If a top-of-file module docstring begins at start_idx, return (doc_start, doc_end)
  inclusive indices. Otherwise (None, None).

  Accepts only top-of-file module docstrings using triple quotes (single-quote or
  double-quote variants) as the first statement.
  """
  if start_idx >= len(lines):
    return (None, None)

  line = lines[start_idx].lstrip()
  if line.startswith('"""') or line.startswith("'''"):
    quote = '"""' if line.startswith('"""') else "'''"

    if line.count(quote) >= 2:
      return (start_idx, start_idx)

    for j in range(start_idx + 1, min(len(lines), start_idx + 200)):
      if quote in lines[j]:
        return (start_idx, j)

    die(f"{TARGET}: unterminated module docstring within first 200 lines")

  return (None, None)


def header_scan_start(lines: list[str]) -> int:
  i = 0
  if i < len(lines) and is_shebang(lines[i]):
    i += 1
  if i < len(lines) and is_encoding(lines[i]):
    i += 1
  return i


def first_nontrivia(lines: list[str], start: int) -> int:
  i = start
  while i < len(lines) and (is_blank(lines[i]) or is_comment(lines[i])):
    i += 1
  return i


def first_code_statement(lines: list[str]) -> int:
  i = header_scan_start(lines)
  i = first_nontrivia(lines, i)

  doc_s, doc_e = parse_top_module_docstring(lines, i)
  if doc_s is not None:
    i = doc_e + 1

  while i < len(lines):
    if is_blank(lines[i]) or is_comment(lines[i]):
      i += 1
      continue
    if is_import(lines[i]):
      i += 1
      continue
    break
  return i


def marker_state(lines: list[str]) -> tuple[int | None, int | None]:
  name_idx = None
  doc_idx = None
  for i, line in enumerate(lines):
    if "SV_CONTRACT_NAME:" in line:
      if line.strip() != NAME_LINE:
        die(f"{TARGET}: existing SV_CONTRACT_NAME line mismatch")
      name_idx = i
    if "SV_CONTRACT_DOC_PATH:" in line:
      if line.strip() != DOC_LINE:
        die(f"{TARGET}: existing SV_CONTRACT_DOC_PATH line mismatch")
      doc_idx = i

  if (name_idx is None) ^ (doc_idx is None):
    die(f"{TARGET}: partial contract marker present (one of two lines missing)")

  return (name_idx, doc_idx)


def ensure_markers() -> None:
  if not TARGET.exists():
    die(f"missing target file: {TARGET}")

  raw = TARGET.read_text(encoding="utf-8")
  lines_ke = raw.splitlines(True)
  lines = [l.rstrip("\n") for l in lines_ke]

  name_idx, doc_idx = marker_state(lines_ke)
  code_idx = first_code_statement(lines)

  if name_idx is not None and name_idx >= code_idx:
    die(f"{TARGET}: markers present after executable code; refuse")

  if name_idx is not None and doc_idx is not None:
    return

  i = header_scan_start(lines)
  i = first_nontrivia(lines, i)
  doc_s, doc_e = parse_top_module_docstring(lines, i)

  if doc_s is not None:
    insert_at = doc_e + 1
  else:
    if i >= len(lines):
      die(f"{TARGET}: unexpected empty file shape")
    if not is_import(lines[i]):
      die(f"{TARGET}: expected top-of-file import or module docstring; found unexpected header shape")
    insert_at = i

  marker_block = [NAME_LINE + "\n", DOC_LINE + "\n", "\n"]
  new_lines = lines_ke[:insert_at] + marker_block + lines_ke[insert_at:]
  TARGET.write_text("".join(new_lines), encoding="utf-8")


def main() -> None:
  before = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
  ensure_markers()
  after = TARGET.read_text(encoding="utf-8")
  if before != after:
    print(f"OK: inserted contract markers into {TARGET}")
  else:
    print(f"OK: already compliant: {TARGET}")


if __name__ == "__main__":
  main()
