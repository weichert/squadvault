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


def _git_ls_files(root: Path, patterns: list[str]) -> list[Path]:
    cmd = ["git", "ls-files"] + patterns
    out = subprocess.run(
        cmd,
        cwd=str(root),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout
    files = [root / line.strip() for line in out.splitlines() if line.strip()]
    return files


def _is_exempt(p: Path) -> bool:
    # Explicit, local, auditable escape hatch.
    # If a file truly must be unpaired, it must declare:
    #   SV_PATCH_PAIR_EXEMPT
    try:
        return "SV_PATCH_PAIR_EXEMPT" in _read_text(p)
    except FileNotFoundError:
        return False


def main() -> int:
    root = _repo_root()

    gate_path = root / "scripts" / "check_patch_pairs_v1.sh"
    gate_text = """#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

fail=0

echo "==> Gate: patcher/wrapper pairing (v1)"
echo "    rule: scripts/patch_*.sh <-> scripts/_patch_*.py (unless SV_PATCH_PAIR_EXEMPT)"

# Use tracked files only (prevents local junk from affecting CI).
wrappers="$(git ls-files 'scripts/patch_*.sh' || true)"
patchers="$(git ls-files 'scripts/_patch_*.py' || true)"

missing_pairs=0

check_pair() {
  local src="$1"
  local expected="$2"

  if grep -q 'SV_PATCH_PAIR_EXEMPT' "$src" 2>/dev/null; then
    echo "SKIP (exempt): $src"
    return 0
  fi

  if [ ! -f "$expected" ]; then
    echo "ERROR: missing pair for $src"
    echo "       expected: $expected"
    missing_pairs=1
    return 0
  fi

  if grep -q 'SV_PATCH_PAIR_EXEMPT' "$expected" 2>/dev/null; then
    echo "ERROR: pair exists but is exempt (forbidden mismatch)"
    echo "       src: $src"
    echo "       pair: $expected (contains SV_PATCH_PAIR_EXEMPT)"
    missing_pairs=1
    return 0
  fi
}

# Wrapper -> patcher
if [ -n "$wrappers" ]; then
  echo "$wrappers" | while IFS= read -r w; do
    [ -z "$w" ] && continue
    base="$(basename "$w")"           # patch_foo_v1.sh
    stem="${base%.sh}"               # patch_foo_v1
    expected="scripts/_${stem}.py"   # scripts/_patch_foo_v1.py
    check_pair "$w" "$expected"
  done
fi

# Patcher -> wrapper
if [ -n "$patchers" ]; then
  echo "$patchers" | while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="$(basename "$p")"          # _patch_foo_v1.py
    stem="${base%.py}"               # _patch_foo_v1
    if [ "${stem#_}" = "$stem" ]; then
      # Should never happen with our glob, but keep fail-closed.
      echo "ERROR: unexpected patcher name (missing leading underscore): $p"
      missing_pairs=1
      continue
    fi
    expected="scripts/${stem#_}.sh"  # scripts/patch_foo_v1.sh
    check_pair "$p" "$expected"
  done
fi

if [ "$missing_pairs" -ne 0 ]; then
  echo "FAIL: patcher/wrapper pairing gate failed."
  echo "      Fix by adding the missing counterpart, or (rarely) adding SV_PATCH_PAIR_EXEMPT."
  exit 1
fi

echo "OK: patcher/wrapper pairing gate passed."
"""

    prove_ci_path = root / "scripts" / "prove_ci.sh"
    if not prove_ci_path.exists():
        print("FATAL: scripts/prove_ci.sh not found", file=sys.stderr)
        return 2
    prove_ci_text = _read_text(prove_ci_path)

    # Anchor must be stable: insert right after the filesystem ordering gate success marker if present,
    # otherwise after "== CI Proof Suite ==" line.
    insertion = """
echo "==> Ops: patcher/wrapper pairing gate"
bash scripts/check_patch_pairs_v1.sh
"""

    if "bash scripts/check_patch_pairs_v1.sh" not in prove_ci_text:
        if "==> Filesystem ordering determinism gate" in prove_ci_text:
            # Insert after the filesystem ordering gate block by finding the first occurrence of its OK line.
            marker = "OK: filesystem ordering determinism gate passed."
            if marker in prove_ci_text:
                prove_ci_text = prove_ci_text.replace(marker, marker + insertion, 1)
            else:
                # Fall back to inserting after suite header.
                hdr = "== CI Proof Suite =="
                if hdr in prove_ci_text:
                    prove_ci_text = prove_ci_text.replace(hdr, hdr + insertion, 1)
                else:
                    print("FATAL: could not find insertion anchor in scripts/prove_ci.sh", file=sys.stderr)
                    return 3
        else:
            hdr = "== CI Proof Suite =="
            if hdr in prove_ci_text:
                prove_ci_text = prove_ci_text.replace(hdr, hdr + insertion, 1)
            else:
                print("FATAL: could not find suite header anchor in scripts/prove_ci.sh", file=sys.stderr)
                return 3

    docs_gate_path = root / "docs" / "80_indices" / "ops" / "CI_Patcher_Wrapper_Pairing_Gate_v1.0.md"
    docs_gate_text = """# CI Patcher/Wrapper Pairing Gate (v1.0)

Status: CANONICAL (Ops/CI Guardrail)

## Purpose

Enforce SquadVault's non-negotiable operational convention:

- All changes must be implementable via a **versioned patcher** (`scripts/_patch_*.py`)
- and a **versioned wrapper** (`scripts/patch_*.sh`)

This gate prevents drift where a patcher exists without an executable wrapper (or vice-versa).

## Enforcement

- Gate script: `scripts/check_patch_pairs_v1.sh`
- CI entrypoint: `scripts/prove_ci.sh`

## Rule

For tracked files:

- `scripts/patch_<name>.sh` MUST have `scripts/_patch_<name>.py`
- `scripts/_patch_<name>.py` MUST have `scripts/patch_<name>.sh`

Exception (rare):

A file may opt out only by containing the explicit marker:

- `SV_PATCH_PAIR_EXEMPT`

This is an auditable, local escape hatch and should be used sparingly.
"""

    idx_path = root / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
    if not idx_path.exists():
        print("FATAL: docs/80_indices/ops/CI_Guardrails_Index_v1.0.md not found", file=sys.stderr)
        return 4
    idx_text = _read_text(idx_path)
    link_line = "- [CI Patcher/Wrapper Pairing Gate (v1.0)](CI_Patcher_Wrapper_Pairing_Gate_v1.0.md)\n"
    if link_line not in idx_text:
        # Append under an "Ops" style list if present; otherwise append at end.
        idx_text = idx_text.rstrip() + "\n" + link_line

    changed = False
    changed |= _write_text_if_changed(gate_path, gate_text)
    changed |= _write_text_if_changed(prove_ci_path, prove_ci_text)
    changed |= _write_text_if_changed(docs_gate_path, docs_gate_text)
    changed |= _write_text_if_changed(idx_path, idx_text)

    # Ensure gate is executable for operator ergonomics (CI calls via bash, but keep it consistent).
    try:
        gate_path.chmod(0o755)
    except Exception:
        # Don't fail on chmod issues; content correctness is the invariant.
        pass

    if not changed:
        print("OK: no changes needed (already applied).")
    else:
        print("OK: patch applied.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
