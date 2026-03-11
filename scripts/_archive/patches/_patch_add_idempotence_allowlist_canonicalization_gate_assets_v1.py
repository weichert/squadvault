from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

PATCHER = REPO_ROOT / "scripts" / "_patch_canonicalize_patch_idempotence_allowlist_v1.py"
WRAPPER = REPO_ROOT / "scripts" / "patch_canonicalize_patch_idempotence_allowlist_v1.sh"
GATE = REPO_ROOT / "scripts" / "gate_patch_idempotence_allowlist_canonical_v1.sh"

PATCHER_TEXT = """from __future__ import annotations

from pathlib import Path
import sys

ALLOWLIST = Path("scripts/patch_idempotence_allowlist_v1.txt")

def norm_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    # stable canonical order + unique
    out = sorted(set(out))
    return out

def main() -> int:
    if not ALLOWLIST.exists():
        raise SystemExit(f"REFUSE: missing allowlist: {ALLOWLIST}")

    src = ALLOWLIST.read_text(encoding="utf-8")
    lines = norm_lines(src)

    header = "# SquadVault — idempotence allowlist (v1)\\n# One wrapper path per line. Comments (#) and blank lines ignored.\\n\\n"
    new_text = header + "\\n".join(lines) + ("\\n" if lines else "")

    if src == new_text:
        return 0

    ALLOWLIST.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
"""

WRAPPER_TEXT = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: canonicalize patch_idempotence_allowlist_v1.txt (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_canonicalize_patch_idempotence_allowlist_v1.py

echo "==> done"
"""

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: idempotence allowlist canonical (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

ALLOWLIST="scripts/patch_idempotence_allowlist_v1.txt"
if [[ ! -f "${ALLOWLIST}" ]]; then
  echo "ERROR: missing allowlist: ${ALLOWLIST}" >&2
  exit 2
fi

items=()
while IFS= read -r raw; do
  line="${raw#"${raw%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  [[ -z "${line}" ]] && continue
  [[ "${line}" == \\#* ]] && continue

  if [[ "${raw}" != "${line}" ]]; then
    echo "ERROR: allowlist line has leading/trailing whitespace:" >&2
    echo "  raw: ${raw}" >&2
    exit 3
  fi

  items+=("${line}")
done < "${ALLOWLIST}"

if [[ "${#items[@]}" -eq 0 ]]; then
  echo "ERROR: allowlist is empty: ${ALLOWLIST}" >&2
  exit 4
fi

missing=0
for p in "${items[@]}"; do
  if [[ ! -f "${p}" ]]; then
    echo "ERROR: allowlist references missing file: ${p}" >&2
    missing=1
  fi
done
[[ "${missing}" -ne 0 ]] && exit 5

tmp="$(mktemp -t sv_allowlist.XXXXXX 2>/dev/null || mktemp -t sv_allowlist)"
trap 'rm -f "${tmp}"' EXIT
printf "%s\\n" "${items[@]}" > "${tmp}"

dups="$(sort "${tmp}" | uniq -d || true)"
if [[ -n "${dups}" ]]; then
  echo "ERROR: allowlist contains duplicates:" >&2
  echo "${dups}" >&2
  exit 6
fi

sorted_tmp="$(mktemp -t sv_allowlist_sorted.XXXXXX 2>/dev/null || mktemp -t sv_allowlist_sorted)"
trap 'rm -f "${tmp}" "${sorted_tmp}"' EXIT
sort "${tmp}" > "${sorted_tmp}"

if ! cmp -s "${tmp}" "${sorted_tmp}"; then
  echo "ERROR: allowlist is not sorted canonically (LC_ALL=C): ${ALLOWLIST}" >&2
  echo "Hint: run: bash scripts/patch_canonicalize_patch_idempotence_allowlist_v1.sh" >&2
  exit 7
fi

echo "OK: allowlist is canonical (sorted, unique, existing files, no stray whitespace)."
"""

def write_if_needed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cur = path.read_text(encoding="utf-8") if path.exists() else None
    if cur == text:
        return
    path.write_text(text, encoding="utf-8")

def main() -> int:
    write_if_needed(PATCHER, PATCHER_TEXT)
    write_if_needed(WRAPPER, WRAPPER_TEXT)
    write_if_needed(GATE, GATE_TEXT)
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
