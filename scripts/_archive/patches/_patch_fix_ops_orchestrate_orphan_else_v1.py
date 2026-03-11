from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/ops_orchestrate.sh")

# This is the broken tail we want to remove/replace (as seen in your nl output).
BAD = """\
  echo "=== Prove: scripts/prove_ci.sh ==="
  ./scripts/prove_ci.sh
else
  if [[ -n "$(git status --porcelain)" ]]; then
    die "tree not clean after successful run; use --commit or revert changes"
  fi

  echo
  echo "=== Prove: scripts/prove_ci.sh ==="
  ./scripts/prove_ci.sh
fi
"""

GOOD = """\
# If we did not commit, then we must not leave a dirty tree after applying a patch.
if [[ "${commit_enabled}" != "1" && "${pass1_changed}" == "1" ]]; then
  die "tree not clean after successful run; use --commit or revert changes"
fi

echo
echo "=== Prove: scripts/prove_ci.sh ==="
./scripts/prove_ci.sh
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if GOOD in s:
        print("OK: ops_orchestrate orphan-else fix already applied (v1).")
        return

    if BAD not in s:
        # Show a helpful excerpt near the end so we can adjust anchors if needed.
        lines = s.splitlines()
        start = max(0, len(lines) - 80)
        excerpt = "\n".join(f"{i+1:4d}  {lines[i]}" for i in range(start, len(lines)))
        raise SystemExit(
            "ERROR: could not locate expected orphan-else prove tail block (v1).\n"
            "---- tail (last ~80 lines) ----\n"
            f"{excerpt}\n"
            "---- end tail ----"
        )

    TARGET.write_text(s.replace(BAD, GOOD), encoding="utf-8")
    print("OK: patched ops_orchestrate orphan else + prove flow (v1).")


if __name__ == "__main__":
    main()
