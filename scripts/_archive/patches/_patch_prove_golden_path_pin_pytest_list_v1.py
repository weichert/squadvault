from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

# We replace the broad run:
#   pytest -q Tests
#
# with a pinned, tracked allowlist via git ls-files:
#   mapfile -t gp_tests < <(git ls-files 'Tests/test_*.py' | sort)
#   pytest -q "${gp_tests[@]}"
#
# This prevents the golden path from silently growing as new tests are added.

NEEDLE = "pytest -q Tests\n"

REPLACEMENT = """\
# SV_PATCH: pinned, git-tracked pytest list (avoid broad `pytest -q Tests`)
if command -v git >/dev/null 2>&1; then
  # Prefer a stable, deterministic order.
  # We rely on git-tracked tests only to avoid picking up untracked/renamed files.
  if command -v sort >/dev/null 2>&1; then
    mapfile -t gp_tests < <(git ls-files 'Tests/test_*.py' | sort)
  else
    mapfile -t gp_tests < <(git ls-files 'Tests/test_*.py')
  fi

  if [[ "${#gp_tests[@]}" -eq 0 ]]; then
    echo "ERROR: no git-tracked Tests/test_*.py files found for golden path" >&2
    exit 1
  fi

  pytest -q "${gp_tests[@]}"
else
  # Fallback (should not happen in CI, but keeps local runs resilient).
  pytest -q Tests
fi
# /SV_PATCH: pinned, git-tracked pytest list
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if REPLACEMENT in s:
        print("OK: prove_golden_path pinned pytest list already applied (v1).")
        return

    if NEEDLE not in s:
        # Helpful tail for anchor debugging if upstream changed.
        tail = "\n".join(s.splitlines()[-80:])
        raise SystemExit(
            "ERROR: could not locate expected 'pytest -q Tests' line in prove_golden_path.sh (v1)\n"
            "---- tail (last ~80 lines) ----\n"
            f"{tail}\n"
            "---- end tail ----"
        )

    TARGET.write_text(s.replace(NEEDLE, REPLACEMENT, 1), encoding="utf-8")
    print("OK: patched prove_golden_path to use pinned tracked pytest list (v1).")

if __name__ == "__main__":
    main()
