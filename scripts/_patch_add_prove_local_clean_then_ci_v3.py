from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_local_clean_then_ci_v3.sh")
INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

SCRIPT_TEXT = """#!/usr/bin/env bash
# SquadVault — local scratch cleanup + CI prove helper (v3)
#
# Local-only helper. NOT invoked by CI.
#
# Tightened cleanup scope (v3):
#   ONLY untracked files matching the explicit scratch marker patterns:
#     - scripts/_patch__*.py
#     - scripts/patch__*.sh
#
# Default is dry-run:
#   - Prints exactly what it would remove (deterministic ordering)
#   - Exits nonzero if junk is present
#
# Destructive mode:
#   - Requires SV_LOCAL_CLEAN=1
#   - Deletes ONLY the listed untracked scratch files
#   - Then runs: bash scripts/prove_ci.sh
#
# Notes:
#   - CWD-independent: resolves repo root via git rev-parse --show-toplevel
#   - bash3-safe: no mapfile, no assoc arrays
#   - Safety: ONLY untracked files are candidates (tracked files are never removed)

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

echo "== Local cleaner scope (v3) =="
echo "Candidates are ONLY *untracked* files matching:"
echo "  - scripts/_patch__*.py"
echo "  - scripts/patch__*.sh"
echo "Tracked files are never removed."
echo

junk_list="$(
  git ls-files --others --exclude-standard \
    | grep -E '^(scripts/_patch__.*\\.py|scripts/patch__.*\\.sh)$' \
    | sort
)" || true

if [ -n "${junk_list}" ]; then
  echo "== Local scratch artifacts detected (untracked) =="
  echo "${junk_list}"
  echo

  if [ "${SV_LOCAL_CLEAN:-0}" != "1" ]; then
    echo "Dry-run mode (no deletions)."
    echo "To delete ONLY the files listed above and then run prove_ci:"
    echo "  SV_LOCAL_CLEAN=1 bash scripts/prove_local_clean_then_ci_v3.sh"
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

INDEX_BULLET_V3 = (
  "- `scripts/prove_local_clean_then_ci_v3.sh` — local-only helper: cleans *only* "
  "untracked scratch files named `scripts/_patch__*.py` and `scripts/patch__*.sh` "
  "(dry-run by default; requires `SV_LOCAL_CLEAN=1` to delete), then runs "
  "`bash scripts/prove_ci.sh`\\n"
)

INDEX_SNIPPET_V3 = (
  "## Local-only helpers (not invoked by CI)\\n\\n"
  + INDEX_BULLET_V3
)


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

  if "prove_local_clean_then_ci_v3.sh" in txt:
    return

  if "## Local-only helpers (not invoked by CI)" in txt:
    parts = txt.split("## Local-only helpers (not invoked by CI)")
    head = parts[0]
    tail = "## Local-only helpers (not invoked by CI)" + parts[1]
    lines = tail.splitlines(True)

    out = []
    out.append(lines[0])  # header

    if len(lines) > 1 and lines[1].strip() == "":
      out.append(lines[1])
      rest = lines[2:]
    else:
      out.append("\\n")
      rest = lines[1:]

    filtered_rest = []
    for ln in rest:
      if "prove_local_clean_then_ci_v1.sh" in ln:
        continue
      if "prove_local_clean_then_ci_v2.sh" in ln:
        continue
      filtered_rest.append(ln)

    out.append(INDEX_BULLET_V3)
    if filtered_rest and filtered_rest[0].strip() != "":
      out.append("\\n")
    out.extend(filtered_rest)

    path.write_text(head + "".join(out), encoding="utf-8")
    return

  if not txt.endswith("\\n"):
    txt += "\\n"
  txt += "\\n" + INDEX_SNIPPET_V3
  path.write_text(txt, encoding="utf-8")


def main() -> None:
  write_file_refuse_on_diff(TARGET, SCRIPT_TEXT)
  patch_index_if_present(INDEX)
  print("OK: wrote scripts/prove_local_clean_then_ci_v3.sh")
  if INDEX.exists():
    print("OK: checked/updated docs index for discoverability:", INDEX)


if __name__ == "__main__":
  main()
