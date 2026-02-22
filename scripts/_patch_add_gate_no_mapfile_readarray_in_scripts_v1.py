from __future__ import annotations

from pathlib import Path
import stat
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _repo_root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


_GATE = r"""#!/usr/bin/env bash
set -euo pipefail

# === Gate: No mapfile/readarray in CI execution scripts/ (v1) ===
#
# macOS default bash is 3.2; mapfile/readarray are not available.
# Enforce only on CI execution surfaces (prove/gate/check), not patch wrappers or archives.
#
# Scope (tracked):
#   - scripts/prove_*.sh
#   - scripts/gate_*.sh
#   - scripts/check_*.sh
#
# Ignore:
#   - comment-only lines (after grep -n => "NN:# ...")
#   - this gate file itself (to avoid self-matches)

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"
cd "$REPO_ROOT"

THIS="scripts/gate_no_mapfile_readarray_in_scripts_v1.sh"

fail=0
violations=""

while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ "$f" = "$THIS" ] && continue

  # ignore comment-only lines, but flag real usage
  if grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" \
      | grep -vE '^[0-9]+:[[:space:]]*#' >/dev/null; then
    violations+="$f:\n"
    violations+="$(grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" | grep -vE '^[0-9]+:[[:space:]]*#')\n"
    fail=1
  fi
done < <(
  git ls-files \
    "scripts/prove_*.sh" \
    "scripts/gate_*.sh" \
    "scripts/check_*.sh"
)

if [ "$fail" -ne 0 ]; then
  echo "FAIL: forbidden bash4-only builtins found in tracked CI execution scripts (mapfile/readarray)."
  echo
  # shellcheck disable=SC2059
  printf "%b" "$violations"
  exit 1
fi

echo "OK: no mapfile/readarray found in tracked CI execution scripts (v1)."
"""


def _ensure_gate() -> None:
    root = _repo_root()
    rel = "scripts/gate_no_mapfile_readarray_in_scripts_v1.sh"
    p = root / rel
    desired = _GATE.rstrip() + "\n"
    if p.exists() and _read(p) == desired:
        _chmod_x(p)
        return
    _clipwrite(rel, desired)
    _chmod_x(p)


def _wire_prove_ci() -> None:
    root = _repo_root()
    prove = root / "scripts" / "prove_ci.sh"
    if not prove.exists():
        raise SystemExit("ERROR: scripts/prove_ci.sh not found")

    s = _read(prove)
    if "scripts/gate_no_mapfile_readarray_in_scripts_v1.sh" in s:
        return

    block = (
        'echo "=== Gate: Bash 3.2 builtin compatibility (v1) ==="\n'
        "bash scripts/gate_no_mapfile_readarray_in_scripts_v1.sh\n"
    )

    lines = s.splitlines(keepends=True)

    for i, ln in enumerate(lines):
        if "gate_no_xtrace_guardrail_v1.sh" in ln:
            lines.insert(i + 1, block)
            _clipwrite("scripts/prove_ci.sh", "".join(lines))
            return

    for i, ln in enumerate(lines):
        if "== CI Proof Suite ==" in ln:
            lines.insert(i + 1, block)
            _clipwrite("scripts/prove_ci.sh", "".join(lines))
            return

    raise SystemExit("ERROR: no safe insertion point found in prove_ci.sh (refusing).")


def _index_ops_guardrails() -> None:
    root = _repo_root()
    idx_rel = "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
    idx = root / idx_rel
    if not idx.exists():
        raise SystemExit(f"ERROR: missing {idx_rel}")

    begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
    end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

    s = _read(idx)
    if begin not in s or end not in s:
        raise SystemExit("ERROR: bounded entrypoints markers not found (refusing).")

    entry = "- scripts/gate_no_mapfile_readarray_in_scripts_v1.sh — Bash 3.2 compatibility: forbid mapfile/readarray in scripts/ (v1)\n"
    if entry in s:
        return

    pre, rest = s.split(begin, 1)
    mid, post = rest.split(end, 1)
    if not mid.endswith("\n"):
        mid += "\n"
    mid += entry
    out = pre + begin + mid + end + post
    _clipwrite(idx_rel, out)


def main() -> int:
    _ensure_gate()
    _wire_prove_ci()
    _index_ops_guardrails()
    print("OK: added no-mapfile/readarray gate + wiring + index entry (idempotent).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
