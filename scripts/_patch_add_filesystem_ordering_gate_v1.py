#!/usr/bin/env python3
from pathlib import Path
import os
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK = REPO_ROOT / "scripts" / "check_filesystem_ordering_determinism.sh"
PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"

CHECK_BODY = """#!/usr/bin/env bash
set -euo pipefail

# === SquadVault: Filesystem Ordering Determinism Gate (v1) ===
# Detect common unordered filesystem iteration patterns in scripts/ and src/.
# Waiver (explicit, reviewable):
#   # SV_ALLOW_UNSORTED_FS_ORDER

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

FAIL=0
say() { echo "$@"; }
warn() { echo "ERROR: $@" 1>&2; }

grep_hits() {
  local label="$1"
  local re="$2"
  shift 2

  local hits
  hits="$(grep -R -n -E "${re}" "$@" 2>/dev/null || true)"

  if [ -n "${hits}" ]; then
    hits="$(printf "%s\\n" "${hits}" | grep -v "SV_ALLOW_UNSORTED_FS_ORDER" || true)"
  fi

  if [ -n "${hits}" ]; then
    warn "Filesystem ordering nondeterminism risk: ${label}"
    printf "%s\\n" "${hits}" 1>&2
    FAIL=1
  fi
}

TARGETS_SHELL="scripts"
TARGETS_PY="src scripts"

grep_hits "shell: 'ls | ...' (ordering + whitespace hazards)" \
  '(^|[[:space:];&(])ls([[:space:]].*)?[[:space:]]*\\|' \
  ${TARGETS_SHELL}

grep_hits "shell: 'for x in *' (glob order as implicit contract)" \
  'for[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]+in[[:space:]]+[^;]*\\*' \
  ${TARGETS_SHELL}

grep_hits "shell: 'find ... | while read' (traversal order)" \
  'find[[:space:]].*\\|[[:space:]]*while[[:space:]]+read' \
  ${TARGETS_SHELL}

grep_hits "python: os.listdir() used (must sort)" \
  'os\\.listdir[[:space:]]*\\(' \
  ${TARGETS_PY}

grep_hits "python: glob.glob() used (must sort)" \
  'glob\\.glob[[:space:]]*\\(' \
  ${TARGETS_PY}

grep_hits "python: Path.glob()/rglob() used (must sort)" \
  '\\.r?glob[[:space:]]*\\(' \
  ${TARGETS_PY}

grep_hits "python: os.walk() used (must sort dirnames/filenames)" \
  'os\\.walk[[:space:]]*\\(' \
  ${TARGETS_PY}

if [ "${FAIL}" -ne 0 ]; then
  echo 1>&2
  warn "Filesystem ordering determinism gate FAILED."
  warn "Fix by sorting explicitly (e.g., 'sorted(...)', '.sort()', '... | sort'),"
  warn "or add waiver only if ordering provably does not matter:"
  warn "  # SV_ALLOW_UNSORTED_FS_ORDER"
  exit 1
fi

say "OK: filesystem ordering determinism gate passed."
"""

def write_if_changed(path: Path, content: str) -> None:
  cur = path.read_text() if path.exists() else None
  if cur == content:
    print(f"OK: unchanged {path}")
    return
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(content)
  os.chmod(path, 0o755)
  print(f"OK: wrote {path}")

def wire_prove_ci() -> None:
  if not PROVE_CI.exists():
    raise SystemExit(f"ERROR: missing {PROVE_CI}")

  txt = PROVE_CI.read_text()
  if "check_filesystem_ordering_determinism.sh" in txt:
    print(f"OK: already wired {PROVE_CI}")
    return

  gate_block = "\n".join([
    'echo "==> Filesystem ordering determinism gate"',
    "./scripts/check_filesystem_ordering_determinism.sh",
    "",
  ])

  lines = txt.splitlines(True)

  # Insert right after the '== CI Proof Suite ==' banner if present; otherwise near top.
  insert_at = None
  for i, line in enumerate(lines):
    if "== CI Proof Suite ==" in line:
      insert_at = i + 1
      break

  if insert_at is None:
    insert_at = 0
    for i, line in enumerate(lines[:60]):
      if re.match(r"^\\s*set\\s+-", line):
        insert_at = i + 1

  lines.insert(insert_at, gate_block)
  PROVE_CI.write_text("".join(lines))
  print(f"OK: patched {PROVE_CI}")

def main():
  write_if_changed(CHECK, CHECK_BODY)
  wire_prove_ci()

if __name__ == "__main__":
  main()
