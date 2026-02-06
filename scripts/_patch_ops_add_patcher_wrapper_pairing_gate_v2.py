from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(p)


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_text_if_changed(p: Path, text: str) -> bool:
    if p.exists() and _read_text(p) == text:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return True


def _git_ls_files(root: Path, patterns: list[str]) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"] + patterns,
        cwd=str(root),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    root = _repo_root()

    allowlist_path = root / "scripts" / "patch_pair_allowlist_v1.txt"

    wrappers = _git_ls_files(root, ["scripts/patch_*.sh"])
    patchers = _git_ls_files(root, ["scripts/_patch_*.py"])

    # Compute legacy mismatches for bootstrap allowlist (tracked + deterministic).
    missing: set[str] = set()

    # wrapper -> expected patcher
    for w in wrappers:
        base = Path(w).name  # patch_foo_v1.sh
        stem = base[:-3]     # patch_foo_v1
        expected = f"scripts/_{stem}.py"
        if expected not in patchers:
            missing.add(w)

    # patcher -> expected wrapper
    for p in patchers:
        base = Path(p).name  # _patch_foo_v1.py
        stem = base[:-3]     # _patch_foo_v1
        if not stem.startswith("_"):
            # defensive; should not happen
            missing.add(p)
            continue
        expected = f"scripts/{stem[1:]}.sh"
        if expected not in wrappers:
            missing.add(p)

    # Bootstrap allowlist contents from current repo state.
    # This makes the new gate enforceable now without rewriting history.
    allowlist_text = (
        "# patch_pair_allowlist_v1.txt\n"
        "# Canonical allowlist for legacy patcher/wrapper pairing exceptions.\n"
        "#\n"
        "# Rule:\n"
        "#   - New unpaired patchers/wrappers MUST NOT be added.\n"
        "#   - If an exception is truly required, add it here (reviewable).\n"
        "#\n"
        "# One path per line, exact match, git-tracked only.\n"
    )
    for path in sorted(missing):
        allowlist_text += path + "\n"

    gate_path = root / "scripts" / "check_patch_pairs_v1.sh"
    gate_text = """#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "==> Gate: patcher/wrapper pairing (v1)"
echo "    rule: scripts/patch_*.sh <-> scripts/_patch_*.py"
echo "    legacy exceptions: scripts/patch_pair_allowlist_v1.txt"

ALLOWLIST="scripts/patch_pair_allowlist_v1.txt"

is_allowlisted() {
  local path="$1"
  [ -f "$ALLOWLIST" ] || return 1
  grep -Fxq "$path" "$ALLOWLIST"
}

wrappers="$(git ls-files 'scripts/patch_*.sh' || true)"
patchers="$(git ls-files 'scripts/_patch_*.py' || true)"

missing_pairs=0

note_missing() {
  local src="$1"
  local expected="$2"

  if is_allowlisted "$src"; then
    echo "ALLOWLISTED: missing pair for $src"
    echo "            expected: $expected"
    return 0
  fi

  echo "ERROR: missing pair for $src"
  echo "       expected: $expected"
  missing_pairs=1
}

# Wrapper -> patcher (avoid pipe subshell; bash 3.2 safe)
if [ -n "$wrappers" ]; then
  while IFS= read -r w; do
    [ -z "$w" ] && continue
    base="$(basename "$w")"           # patch_foo_v1.sh
    stem="${base%.sh}"               # patch_foo_v1
    expected="scripts/_${stem}.py"   # scripts/_patch_foo_v1.py
    if [ ! -f "$expected" ]; then
      note_missing "$w" "$expected"
    fi
  done <<< "$wrappers"
fi

# Patcher -> wrapper (avoid pipe subshell; bash 3.2 safe)
if [ -n "$patchers" ]; then
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="$(basename "$p")"          # _patch_foo_v1.py
    stem="${base%.py}"               # _patch_foo_v1
    if [ "${stem#_}" = "$stem" ]; then
      # Defensive: should never happen with our glob, but fail-closed.
      if is_allowlisted "$p"; then
        echo "ALLOWLISTED: unexpected patcher name (missing leading underscore): $p"
      else
        echo "ERROR: unexpected patcher name (missing leading underscore): $p"
        missing_pairs=1
      fi
      continue
    fi
    expected="scripts/${stem#_}.sh"  # scripts/patch_foo_v1.sh
    if [ ! -f "$expected" ]; then
      note_missing "$p" "$expected"
    fi
  done <<< "$patchers"
fi

if [ "$missing_pairs" -ne 0 ]; then
  echo "FAIL: patcher/wrapper pairing gate failed."
  echo "      Fix by adding the missing counterpart, or (rarely) allowlist the path:"
  echo "        $ALLOWLIST"
  exit 1
fi

echo "OK: patcher/wrapper pairing gate passed."
"""

    prove_ci_path = root / "scripts" / "prove_ci.sh"
    if not prove_ci_path.exists():
        print("FATAL: scripts/prove_ci.sh not found", file=sys.stderr)
        return 2
    prove_ci_text = _read_text(prove_ci_path)

    insertion = """
echo "==> Ops: patcher/wrapper pairing gate"
bash scripts/check_patch_pairs_v1.sh
"""

    if "bash scripts/check_patch_pairs_v1.sh" not in prove_ci_text:
        marker = "OK: filesystem ordering determinism gate passed."
        if marker in prove_ci_text:
            prove_ci_text = prove_ci_text.replace(marker, marker + insertion, 1)
        else:
            hdr = "== CI Proof Suite =="
            if hdr in prove_ci_text:
                prove_ci_text = prove_ci_text.replace(hdr, hdr + insertion, 1)
            else:
                print("FATAL: could not find insertion anchor in scripts/prove_ci.sh", file=sys.stderr)
                return 3

    docs_gate_path = root / "docs" / "80_indices" / "ops" / "CI_Patcher_Wrapper_Pairing_Gate_v1.0.md"
    docs_gate_text = """# CI Patcher/Wrapper Pairing Gate (v1.0)

Status: CANONICAL (Ops/CI Guardrail)

## Purpose

Enforce SquadVault's operational convention:

- A **versioned patcher** (`scripts/_patch_*.py`)
- must have a corresponding **versioned wrapper** (`scripts/patch_*.sh`)
- and vice-versa.

This reduces drift and preserves executable traceability.

## Enforcement

- Gate script: `scripts/check_patch_pairs_v1.sh`
- CI entrypoint: `scripts/prove_ci.sh`

## Rule

For tracked files:

- `scripts/patch_<name>.sh` MUST have `scripts/_patch_<name>.py`
- `scripts/_patch_<name>.py` MUST have `scripts/patch_<name>.sh`

## Legacy exceptions (audited)

Historical scripts may be exempted only via the tracked allowlist:

- `scripts/patch_pair_allowlist_v1.txt`

This allowlist is explicit, reviewable, and should not grow without clear rationale.
"""

    idx_path = root / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
    if not idx_path.exists():
        print("FATAL: docs/80_indices/ops/CI_Guardrails_Index_v1.0.md not found", file=sys.stderr)
        return 4
    idx_text = _read_text(idx_path)
    link_line = "- [CI Patcher/Wrapper Pairing Gate (v1.0)](CI_Patcher_Wrapper_Pairing_Gate_v1.0.md)\n"
    if link_line not in idx_text:
        idx_text = idx_text.rstrip() + "\n" + link_line

    changed = False
    changed |= _write_text_if_changed(allowlist_path, allowlist_text)
    changed |= _write_text_if_changed(gate_path, gate_text)
    changed |= _write_text_if_changed(prove_ci_path, prove_ci_text)
    changed |= _write_text_if_changed(docs_gate_path, docs_gate_text)
    changed |= _write_text_if_changed(idx_path, idx_text)

    try:
        gate_path.chmod(0o755)
    except Exception:
        pass

    if not changed:
        print("OK: no changes needed (already applied).")
    else:
        print("OK: patch applied (v2).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
