from __future__ import annotations

from pathlib import Path

F = Path("scripts/prove_golden_path.sh")

def main() -> None:
    if not F.exists():
        raise SystemExit(f"Missing {F}")

    txt = F.read_text(encoding="utf-8")

    # Must be a bash script; refuse otherwise.
    if not txt.startswith("#!/"):
        raise SystemExit("Refusing: missing shebang at top of prove_golden_path.sh")

    # If already uses BASH_SOURCE-based repo root resolution, no-op.
    if 'BASH_SOURCE[0]' in txt and 'REPO_ROOT' in txt and 'cd "${REPO_ROOT}"' in txt:
        return

    lines = txt.splitlines(keepends=True)

    # Find insertion point: immediately after `set -euo pipefail` if present,
    # else after the shebang (line 1).
    set_idx = None
    for i, ln in enumerate(lines[:40]):
        if "set -euo pipefail" in ln:
            set_idx = i
            break

    insert_after = 0
    if set_idx is not None:
        insert_after = set_idx
    else:
        insert_after = 0  # after shebang

    block = [
        "\n",
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n',
        'REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n',
        'cd "${REPO_ROOT}"\n',
        "\n",
    ]

    # Remove common non-CWD-safe patterns anywhere in the first ~60 lines:
    # - cd "$(git rev-parse --show-toplevel)"
    # - REPO_ROOT="$(git rev-parse --show-toplevel)"
    # - REPO_ROOT=$(git rev-parse --show-toplevel)
    # - cd "$REPO_ROOT" where REPO_ROOT came from git rev-parse
    new_lines = []
    removed = 0
    for i, ln in enumerate(lines):
        if i < 80 and "git rev-parse --show-toplevel" in ln:
            removed += 1
            continue
        new_lines.append(ln)

    if removed == 0:
        # We still insert the canonical block, but refuse if there's *another* cwd-sensitive pattern
        # like cd "$(pwd)" is fine; but we won't over-refuse. No removal needed.
        pass

    # Insert block
    out = new_lines[: insert_after + 1] + block + new_lines[insert_after + 1 :]

    # Refuse if we now have multiple cd "${REPO_ROOT}" lines near top (likely messy merge)
    head = "".join(out[:120])
    if head.count('cd "${REPO_ROOT}"') > 1:
        raise SystemExit("Refusing: multiple cd \"${REPO_ROOT}\" occurrences near header; manual review needed.")

    F.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
