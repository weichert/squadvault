from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_local_clean_then_ci_v1.sh")
INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

SCRIPT_TEXT = """#!/usr/bin/env bash
# SquadVault — local scratch cleanup + CI prove helper (v1)
#
# Local-only helper. NOT invoked by CI.
#
# Purpose:
#   - Detect common untracked scratch artifacts from iterative work:
#       scripts/_patch_*.py
#       scripts/patch_*.sh
#   - Print exactly what would be removed (deterministic ordering)
#   - Require SV_LOCAL_CLEAN=1 to actually delete anything
#   - If junk is present and SV_LOCAL_CLEAN!=1, exit nonzero (dry-run fail)
#   - When clean (or after cleaning), run: bash scripts/prove_ci.sh
#
# Notes:
#   - CWD-independent: resolves repo root via git rev-parse --show-toplevel
#   - bash3-safe: no mapfile, no assoc arrays

set -euo pipefail

die() {
  echo "ERROR: $*" 1>&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

need_cmd git
need_cmd grep
need_cmd sort
need_cmd rm

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not in a git repo"
cd "$ROOT"

junk_list="$(
  git ls-files --others --exclude-standard \
    | grep -E '^(scripts/_patch_.*\\.py|scripts/patch_.*\\.sh)$' \
    | sort
)" || true

if [ -n "${junk_list}" ]; then
  echo "== Local scratch artifacts detected (untracked) =="
  echo "${junk_list}"
  echo

  if [ "${SV_LOCAL_CLEAN:-0}" != "1" ]; then
    echo "Dry-run mode (no deletions)."
    echo "To delete ONLY the files listed above and then run prove_ci:"
    echo "  SV_LOCAL_CLEAN=1 bash scripts/prove_local_clean_then_ci_v1.sh"
    exit 2
  fi

  echo "SV_LOCAL_CLEAN=1 set — removing listed scratch artifacts..."
  echo "${junk_list}" | while IFS= read -r p; do
    [ -n "$p" ] || continue
    rm -f -- "$p"
  done
  echo "OK: scratch artifacts removed."
  echo
else
  echo "OK: no matching local scratch artifacts found."
  echo
fi

echo "== Run CI prove suite =="
bash "$ROOT/scripts/prove_ci.sh"
"""

INDEX_SNIPPET = """\
## Local-only helpers (not invoked by CI)

- `scripts/prove_local_clean_then_ci_v1.sh` — detects common untracked scratch patcher/wrapper files (dry-run by default) and then runs `bash scripts/prove_ci.sh`
"""


def write_file_refuse_on_diff(path: Path, content: str) -> None:
  if path.exists():
    existing = path.read_text(encoding="utf-8")
    if existing == content:
      return
    raise SystemExit(f"Refusing to modify existing file with unexpected contents: {path}")
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(content, encoding="utf-8")


def patch_index_if_present(path: Path) -> None:
  if not path.exists():
    return

  txt = path.read_text(encoding="utf-8")

  if "prove_local_clean_then_ci_v1.sh" in txt:
    return

  if "## Local-only helpers (not invoked by CI)" in txt:
    parts = txt.split("## Local-only helpers (not invoked by CI)")
    head = parts[0]
    tail = "## Local-only helpers (not invoked by CI)" + parts[1]

    lines = tail.splitlines(True)
    out = []
    out.append(lines[0])
    if len(lines) > 1 and lines[1].strip() == "":
      out.append(lines[1])
      rest = lines[2:]
    else:
      out.append("\n")
      rest = lines[1:]

    out.append("- `scripts/prove_local_clean_then_ci_v1.sh` — detects common untracked scratch patcher/wrapper files (dry-run by default) and then runs `bash scripts/prove_ci.sh`\n")
    if rest and rest[0].strip() != "":
      out.append("\n")
    out.extend(rest)

    path.write_text(head + "".join(out), encoding="utf-8")
    return

  if not txt.endswith("\n"):
    txt += "\n"
  txt += "\n" + INDEX_SNIPPET
  path.write_text(txt, encoding="utf-8")


def main() -> None:
  write_file_refuse_on_diff(TARGET, SCRIPT_TEXT)
  patch_index_if_present(INDEX)
  print("OK: wrote scripts/prove_local_clean_then_ci_v1.sh")
  if INDEX.exists():
    print("OK: checked/updated docs index for discoverability:", INDEX)


if __name__ == "__main__":
  main()
