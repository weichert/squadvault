from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "scripts" / "gate_patch_wrapper_idempotence_allowlist_v1.sh"

INSERT_MARK = "gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh"
INSERT_LINE = "bash scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh\n"

def main() -> int:
  if not TARGET.exists():
    raise SystemExit(f"REFUSE: missing target: {TARGET}")

  text = TARGET.read_text(encoding="utf-8")
  if INSERT_MARK in text:
    return 0

  anchor = "scripts/patch_idempotence_allowlist_v1.txt"
  if anchor not in text:
    raise SystemExit(f"REFUSE: cannot find allowlist anchor ({anchor}) in {TARGET}")

  lines = text.splitlines(keepends=True)

  insert_at = None
  for i, line in enumerate(lines):
    if anchor in line:
      insert_at = i + 1
      break

  if insert_at is None:
    raise SystemExit("REFUSE: unexpected: anchor scan failed")

  if insert_at > 0 and lines[insert_at - 1].rstrip().endswith("\\"):
    raise SystemExit("REFUSE: anchor line ends with backslash continuation; cannot safely insert")

  snippet = []
  snippet.append("\n")
  snippet.append('echo "==> Guard: allowlist wrappers must not recurse into prove_ci"\n')
  snippet.append(INSERT_LINE)
  snippet.append("\n")

  new_text = "".join(lines[:insert_at] + snippet + lines[insert_at:])
  TARGET.write_text(new_text, encoding="utf-8")
  return 0

if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except SystemExit:
    raise
  except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    raise SystemExit(1)
