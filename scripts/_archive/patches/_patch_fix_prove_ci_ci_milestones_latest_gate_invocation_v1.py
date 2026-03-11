from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

OLD = 'bash "$REPO_ROOT/scripts/gate_ci_milestones_latest_block_v1.sh"'
NEW = "bash scripts/gate_ci_milestones_latest_block_v1.sh"

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")

    if NEW in text and OLD not in text:
        print("OK: prove_ci CI_MILESTONES Latest gate invocation already canonical (noop)")
        return

    if OLD not in text:
        raise SystemExit("ERR: expected legacy REPO_ROOT-based invocation not found; refusing to guess")

    new = text.replace(OLD, NEW)
    if new == text:
        print("OK: no changes needed (noop)")
        return

    PROVE.write_text(new, encoding="utf-8")
    print("OK: prove_ci CI_MILESTONES Latest gate invocation patched (REPO_ROOT-free)")

if __name__ == "__main__":
    main()
