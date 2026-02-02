from __future__ import annotations

from pathlib import Path


TARGET = Path("scripts/prove_signal_scout_tier1_type_a_v1.sh")

MARKER = "# SV_PATCH: pinned, git-tracked pytest list (avoid broad directory invocation)\n"

NEW_BLOCK = """\
# SV_PATCH: pinned, git-tracked pytest list (avoid broad directory invocation)
  {
    # Bash-3-safe pinned, git-tracked pytest list.
    # We explicitly enumerate git-tracked Tests/validation/signals/test_*.py files
    # to prevent accidental surface expansion.
    ss_tests=()
    while IFS= read -r p; do
      ss_tests+=("$p")
    done < <(git ls-files 'Tests/validation/signals/test_*.py' | sort)

    if [ "${#ss_tests[@]}" -eq 0 ]; then
      echo "ERROR: no git-tracked Tests/validation/signals/test_*.py files found for Signal Scout Tier-1 proof" >&2
      exit 1
    fi

    "${REPO_ROOT}/scripts/py" -m pytest -q "${ss_tests[@]}"
  }

# /SV_PATCH: pinned, git-tracked pytest list
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print("OK: already patched (marker present).")
        return

    # Find the existing broad invocation and replace it.
    broad = '"${REPO_ROOT}/scripts/py" -m pytest -q "${REPO_ROOT}/Tests/validation/signals"\n'
    if broad not in text:
        raise SystemExit("ERROR: could not find broad pytest directory invocation to replace")

    text2 = text.replace(broad, NEW_BLOCK)

    TARGET.write_text(text2, encoding="utf-8")
    print("OK: patched prove_signal_scout_tier1_type_a_v1.sh to use pinned git-tracked test list (v1)")


if __name__ == "__main__":
    main()
