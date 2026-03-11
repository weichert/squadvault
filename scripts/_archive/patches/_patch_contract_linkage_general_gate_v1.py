from __future__ import annotations

from pathlib import Path
import glob
import sys

REPO = Path(__file__).resolve().parent.parent

SCRIPTS = REPO / "scripts"
OPS_INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

GENERAL_GATE = SCRIPTS / "gate_contract_linkage_v1.sh"

# Keep RC gate as a compatibility wrapper. Discover it.
RC_CANDIDATES = sorted(
    [Path(p) for p in glob.glob(str(SCRIPTS / "gate_*rivalry*chronicle*contract*linkage*_v*.sh"))]
)

OPS_BEGIN = "<!-- SV_CONTRACT_LINKAGE_GATES_v1_BEGIN -->"
OPS_END = "<!-- SV_CONTRACT_LINKAGE_GATES_v1_END -->"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def _insert_bounded_block(doc: Path, begin: str, end: str, block: str) -> None:
    txt = _read(doc)
    if begin in txt and end in txt:
        pre, rest = txt.split(begin, 1)
        _, post = rest.split(end, 1)
        new_txt = pre + begin + "\n" + block.rstrip() + "\n" + end + post
        if new_txt != txt:
            _write(doc, new_txt)
        return

    # If bounded section doesn't exist, append it near end (idempotent, explicit).
    new_txt = txt.rstrip() + "\n\n" + begin + "\n" + block.rstrip() + "\n" + end + "\n"
    _write(doc, new_txt)


def main() -> int:
    if not (REPO / ".git").exists():
        print("ERR: must run inside repo (expected .git at repo root).", file=sys.stderr)
        return 2

    if not OPS_INDEX.exists():
        print(f"ERR: missing ops index: {OPS_INDEX}", file=sys.stderr)
        return 2

    # 1) Write general gate (canonical v1)
    gate = """#!/usr/bin/env bash
set -euo pipefail

# Contract Linkage Gate (v1)
# Enforces that any script claiming a contract includes:
#
# Scope: scripts/*.{sh,py}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

fail() { echo "FAIL: $*" >&2; exit 1; }

TARGET_DIR="scripts"

mapfile -t FILES < <(find "${TARGET_DIR}" -type f \\( -name "*.sh" -o -name "*.py" \\) -print | LC_ALL=C sort)

extract_marker() {
  local file="$1"
  local key="$2"
  local line
  line="$(grep -n -m1 -E "${key}:[[:space:]]*" "${file}" || true)"
  if [[ -z "${line}" ]]; then
    return 0
  fi
  echo "${line#*:}" | sed -E "s/^.*${key}:[[:space:]]*//"
}

bad=0

for f in "${FILES[@]}"; do
  name="$(extract_marker "${f}" "SV_CONTRACT_NAME")"
  doc="$(extract_marker "${f}" "SV_CONTRACT_DOC_PATH")"

  if [[ -n "${name}" || -n "${doc}" ]]; then
    if [[ -z "${name}" ]]; then
      echo "ERR: ${f} declares SV_CONTRACT_DOC_PATH but is missing SV_CONTRACT_NAME" >&2
      bad=1
      continue
    fi
    if [[ -z "${doc}" ]]; then
      echo "ERR: ${f} declares SV_CONTRACT_NAME (${name}) but is missing SV_CONTRACT_DOC_PATH" >&2
      bad=1
      continue
    fi
    if [[ "${doc}" == /* ]]; then
      echo "ERR: ${f} contract doc path must be repo-relative, got: ${doc}" >&2
      bad=1
      continue
    fi
    if [[ ! -f "${doc}" ]]; then
      echo "ERR: ${f} contract doc does not exist: ${doc}" >&2
      bad=1
      continue
    fi
  fi
done

if [[ "${bad}" -ne 0 ]]; then
  fail "contract linkage violations found"
fi

exit 0
"""
    _write(GENERAL_GATE, gate)

    # 2) Convert RC linkage gate into compatibility wrapper
    if len(RC_CANDIDATES) != 1:
        print(
            "ERR: expected exactly one RC linkage gate matching scripts/gate_*contract*linkage*rc*_v*.sh\n"
            f"Found: {', '.join(str(p.name) for p in RC_CANDIDATES) or '(none)'}\n"
            "Action: rename or adjust the discovery glob in this patcher, then re-run.",
            file=sys.stderr,
        )
        return 2

    rc_gate = RC_CANDIDATES[0]
    wrapper = f"""#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper: RC contract linkage gate -> general contract linkage gate (v1)

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
REPO_ROOT="$(cd "${{SCRIPT_DIR}}/.." && pwd)"
cd "${{REPO_ROOT}}"

bash scripts/gate_contract_linkage_v1.sh
"""
    _write(rc_gate, wrapper)

    # 3) Ops index entry (bounded)
    block = """- scripts/gate_contract_linkage_v1.sh — Enforce SV_CONTRACT_* linkage to contract doc paths (v1)
- scripts/{rc_name} — Compatibility wrapper (RC linkage) delegating to gate_contract_linkage_v1.sh (v1)
""".format(rc_name=rc_gate.name)
    _insert_bounded_block(OPS_INDEX, OPS_BEGIN, OPS_END, block)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
