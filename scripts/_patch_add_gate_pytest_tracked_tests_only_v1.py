from __future__ import annotations

from pathlib import Path
import stat
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_text_clipwrite(rel_path: str, content: str) -> None:
    root = _repo_root()
    clipwrite = root / "scripts" / "clipwrite.sh"
    proc = subprocess.run(
        ["bash", str(clipwrite), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


_GATE_BODY = r"""#!/usr/bin/env bash
set -euo pipefail

# === Gate: Pytest must only target tracked Tests/ (v1) ===
#
# Enforces that all pytest invocations in proof/gate/check scripts explicitly
# target Tests/ (tracked paths), never ".", "tests/", absolute paths, or no path.
#
# Scans only tracked:
#   scripts/prove_*.sh
#   scripts/gate_*.sh
#   scripts/check_*.sh
#
# Static enforcement only (grep+token checks). No runtime behavior changes.

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"

cd "$REPO_ROOT"

fail=0
violations=""

mapfile -t TARGETS < <(
  git ls-files \
    "scripts/prove_*.sh" \
    "scripts/gate_*.sh" \
    "scripts/check_*.sh"
)

if [ "${#TARGETS[@]}" -eq 0 ]; then
  echo "ERROR: gate_pytest_tracked_tests_only_v1: no tracked targets found under scripts/{prove_,gate_,check_}*.sh"
  exit 2
fi

is_allowed_tests_path() {
  local tok="$1"
  case "$tok" in
    Tests|Tests/*) return 0 ;;
    *) return 1 ;;
  esac
}

is_forbidden_path() {
  local tok="$1"
  case "$tok" in
    "."|"./"|"./"* ) return 0 ;;
    "tests"|"tests/"|"tests/"* ) return 0 ;;
    /* ) return 0 ;;
    *) return 1 ;;
  esac
}

option_consumes_value() {
  local opt="$1"
  case "$opt" in
    -k|-m|-c|-o|--maxfail|--rootdir|--confcutdir|--basetemp|--override-ini) return 0 ;;
    *) return 1 ;;
  esac
}

check_line_pytest_usage() {
  local file="$1"
  local lineno="$2"
  local line="$3"

  line="${line%%#*}"

  echo "$line" | grep -Eq '(^|[[:space:];&|()])pytest([[:space:]]|$)' || return 0

  if echo "$line" | grep -Eq 'git[[:space:]]+ls-files[[:space:]]+Tests([[:space:]]|$).*xargs[[:space:]]+pytest([[:space:]]|$)'; then
    return 0
  fi

  # shellcheck disable=SC2086
  set -- $line
  local -a toks=("$@")

  local i=0
  local p=-1
  for ((i=0; i<${#toks[@]}; i++)); do
    if [ "${toks[$i]}" = "pytest" ]; then
      p="$i"
      break
    fi
  done
  if [ "$p" -lt 0 ]; then
    return 0
  fi

  local -a args=()
  for ((i=p+1; i<${#toks[@]}; i++)); do
    args+=("${toks[$i]}")
  done

  if [ "${#args[@]}" -eq 0 ]; then
    violations+="${file}:${lineno}: pytest with no explicit path (must target Tests/)\n"
    fail=1
    return 0
  fi

  local idx=0
  while [ "$idx" -lt "${#args[@]}" ]; do
    local a="${args[$idx]}"
    if [[ "$a" == -* ]]; then
      if option_consumes_value "$a"; then
        idx=$((idx+2))
      else
        idx=$((idx+1))
      fi
      continue
    fi
    break
  done

  if [ "$idx" -ge "${#args[@]}" ]; then
    violations+="${file}:${lineno}: pytest options present but no explicit path (must target Tests/)\n"
    fail=1
    return 0
  fi

  local first_path="${args[$idx]}"

  if is_forbidden_path "$first_path"; then
    violations+="${file}:${lineno}: forbidden pytest target '${first_path}' (must target Tests/)\n"
    fail=1
    return 0
  fi

  if ! is_allowed_tests_path "$first_path"; then
    violations+="${file}:${lineno}: pytest target must start with Tests/ (found '${first_path}')\n"
    fail=1
    return 0
  fi
}

for f in "${TARGETS[@]}"; do
  lineno=0
  while IFS= read -r line || [ -n "$line" ]; do
    lineno=$((lineno+1))
    check_line_pytest_usage "$f" "$lineno" "$line"
  done < "$f"
done

if [ "$fail" -ne 0 ]; then
  echo "FAIL: pytest invocations must explicitly target tracked Tests/ paths only."
  echo
  # shellcheck disable=SC2059
  printf "%b" "$violations"
  exit 1
fi

echo "OK: pytest invocations target Tests/ only (tracked)."
"""


def _ensure_gate_file() -> None:
    root = _repo_root()
    rel = "scripts/gate_pytest_tracked_tests_only_v1.sh"
    p = root / rel
    desired = _GATE_BODY.rstrip() + "\n"
    if p.exists() and _read_text(p) == desired:
        _chmod_x(p)
        return
    _write_text_clipwrite(rel, desired)
    _chmod_x(p)


def _patch_prove_ci() -> None:
    root = _repo_root()
    p = root / "scripts" / "prove_ci.sh"
    if not p.exists():
        raise SystemExit("ERROR: scripts/prove_ci.sh not found.")

    s = _read_text(p)
    if "scripts/gate_pytest_tracked_tests_only_v1.sh" in s:
        return

    insert_block = (
        'echo "=== Gate: Pytest must only target tracked Tests/ (v1) ==="\n'
        "bash scripts/gate_pytest_tracked_tests_only_v1.sh\n"
    )

    lines = s.splitlines(keepends=True)

    # Prefer: insert immediately before first uncommented pytest mention
    for i, line in enumerate(lines):
        if "pytest" in line and not line.lstrip().startswith("#"):
            lines.insert(i, insert_block)
            _write_text_clipwrite("scripts/prove_ci.sh", "".join(lines))
            return

    # Fallback: after check_shims_compliance gate if present
    for i, line in enumerate(lines):
        if "scripts/check_shims_compliance.sh" in line:
            lines.insert(i + 1, insert_block)
            _write_text_clipwrite("scripts/prove_ci.sh", "".join(lines))
            return

    raise SystemExit("ERROR: No insertion anchor found in scripts/prove_ci.sh. Refusing.")


def _patch_ci_guardrails_index() -> None:
    root = _repo_root()
    idx = root / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
    if not idx.exists():
        raise SystemExit("ERROR: docs/80_indices/ops/CI_Guardrails_Index_v1.0.md not found.")

    s = _read_text(idx)
    begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
    end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"
    if begin not in s or end not in s:
        raise SystemExit("ERROR: bounded entrypoints section markers not found. Refusing.")

    entry = "- **Pytest must only target tracked `Tests/` paths (v1)** → `scripts/gate_pytest_tracked_tests_only_v1.sh`\n"
    if entry in s:
        return

    pre, rest = s.split(begin, 1)
    mid, post = rest.split(end, 1)
    if not mid.endswith("\n"):
        mid += "\n"
    mid += entry
    out = pre + begin + mid + end + post
    _write_text_clipwrite(str(idx.relative_to(root)), out)


def main() -> int:
    _ensure_gate_file()
    _patch_prove_ci()
    _patch_ci_guardrails_index()
    print("OK: applied pytest-tracked-Tests-only gate + wiring + index entry (idempotent).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
