from __future__ import annotations

from pathlib import Path
import sys


TARGET = Path("scripts/run_golden_path_v1.sh")

NAME_PREFIX = "# SV_CONTRACT_NAME:"
DOC_PREFIX = "# SV_CONTRACT_DOC_PATH:"
DOC_VALUE = "docs/contracts/golden_path_output_contract_v1.md"

REPLACEMENT_LINE = f"# Contract doc (reference): {DOC_VALUE}"


def die(msg: str) -> None:
  print(f"ERROR: {msg}", file=sys.stderr)
  raise SystemExit(2)


def main() -> None:
  if not TARGET.exists():
    die(f"missing target file: {TARGET}")

  raw = TARGET.read_text(encoding="utf-8")
  lines_ke = raw.splitlines(True)
  lines = [l.rstrip("\n") for l in lines_ke]

  # Safety: refuse if someone reintroduced an enforcement marker here.
  for ln in lines:
    if ln.strip().startswith(NAME_PREFIX):
      die(f"{TARGET}: has SV_CONTRACT_NAME marker but is not an enforcement surface; refuse")

  # Find SV_CONTRACT_DOC_PATH marker lines.
  doc_idxs: list[int] = []
  for i, ln in enumerate(lines):
    if ln.strip().startswith(DOC_PREFIX):
      doc_idxs.append(i)

  if len(doc_idxs) > 1:
    die(f"{TARGET}: multiple SV_CONTRACT_DOC_PATH markers found; refuse")

  if len(doc_idxs) == 0:
    # Already removed marker. Ensure a plain reference line exists near the top (optional).
    joined = "\n".join(lines)
    if REPLACEMENT_LINE in joined:
      print(f"OK: already compliant: {TARGET}")
      return
    # If absent, insert after shebang or at top.
    insert_at = 1 if (len(lines_ke) > 0 and lines_ke[0].startswith("#!")) else 0
    block = [REPLACEMENT_LINE + "\n", "\n"]
    lines_ke = lines_ke[:insert_at] + block + lines_ke[insert_at:]
    TARGET.write_text("".join(lines_ke), encoding="utf-8")
    print(f"OK: inserted plain contract doc reference in {TARGET}")
    return

  # Exactly one doc marker found: remove it, and replace with a non-marker comment.
  i = doc_idxs[0]
  existing = lines[i].strip()
  # If it's pointing somewhere else, refuse (we don't want to silently rewrite unrelated markers).
  if DOC_VALUE not in existing:
    die(f"{TARGET}: unexpected SV_CONTRACT_DOC_PATH value; refuse: {existing!r}")

  # Replace the marker line with a plain comment reference.
  lines_ke[i] = REPLACEMENT_LINE + "\n"

  TARGET.write_text("".join(lines_ke), encoding="utf-8")
  print(f"OK: removed SV_CONTRACT_DOC_PATH marker in {TARGET}")


if __name__ == "__main__":
  main()
