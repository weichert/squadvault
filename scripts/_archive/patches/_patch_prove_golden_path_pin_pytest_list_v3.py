from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

BEGIN = "# SV_PATCH: pinned, git-tracked pytest list (avoid broad `pytest -q Tests`)"
END = "# /SV_PATCH: pinned, git-tracked pytest list"

REPLACEMENT = """\
  {
    # Bash-3-safe pinned, git-tracked pytest list.
    # We explicitly enumerate git-tracked Tests/test_*.py files to prevent accidental surface expansion.
    gp_tests=()
    while IFS= read -r p; do
      gp_tests+=("$p")
    done < <(git ls-files 'Tests/test_*.py' | sort)

    if [ "${#gp_tests[@]}" -eq 0 ]; then
      echo "ERROR: no git-tracked Tests/test_*.py files found for golden path" >&2
      exit 1
    fi

    pytest -q "${gp_tests[@]}"
  }
"""

FORBIDDEN_LINE = "pytest -q Tests"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if BEGIN not in s or END not in s:
        raise SystemExit("ERROR: could not locate pinned pytest block markers; refusing")

    pre, rest = s.split(BEGIN, 1)
    _mid, post = rest.split(END, 1)

    new = pre + BEGIN + "\n" + REPLACEMENT + "\n" + END + post

    # Postcondition: forbid *standalone* directory invocation line anywhere.
    for line in new.splitlines():
        if line.strip() == FORBIDDEN_LINE:
            raise SystemExit("ERROR: refusal — standalone forbidden 'pytest -q Tests' remains")

    TARGET.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
