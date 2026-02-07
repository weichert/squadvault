from __future__ import annotations

from pathlib import Path
import sys

GATE = Path("scripts/gate_no_terminal_banner_paste_v1.sh")

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no pasted terminal banners in scripts/ (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# We only scan scripts/, since that's where these pasted banners become dangerous.
# Keep patterns conservative + high-signal to avoid false positives.
patterns=(
  '^Last login: '
  '^The default interactive shell is now zsh\\.'
  '^To update your account to use zsh, please run `chsh -s '
  '^For more details, please visit https://support\\.apple\\.com/kb/HT208050\\.'
  '^Changing shell for '
  '^Password for '
  '^wtmp begins '
)

# Grep all tracked text-like files under scripts/. Avoid __pycache__.
hits=0
for pat in "${patterns[@]}"; do
  # grep exits 1 if no matches, so guard with "|| true"
  out="$(git ls-files 'scripts/*' | grep -v '^scripts/__pycache__/' | xargs -I{} sh -c 'test -f "{}" && printf "%s\\n" "{}"' \
    | xargs grep -nE "${pat}" 2>/dev/null || true)"
  if [[ -n "${out}" ]]; then
    echo "ERROR: found pasted terminal banner lines matching: ${pat}" >&2
    echo "${out}" >&2
    hits=1
  fi
done

if [[ "${hits}" -ne 0 ]]; then
  echo "Hint: remove pasted terminal banner lines from scripts/ (they can execute as commands when copied)." >&2
  exit 2
fi

echo "OK: no pasted terminal banners detected in scripts/."
"""

def main() -> int:
    cur = GATE.read_text(encoding="utf-8") if GATE.exists() else None
    if cur != GATE_TEXT:
        GATE.write_text(GATE_TEXT, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
