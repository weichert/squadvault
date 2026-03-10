from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

NEEDED = 'SV_WORKTREE_SNAP0="$(scripts/gate_worktree_cleanliness_v1.sh begin)"\n'
ANCHOR = 'SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"\n'

def main() -> int:
    text = PROVE.read_text(encoding="utf-8")

    if NEEDED in text:
        print("OK: prove_ci root worktree snapshot init already present (noop)")
        return 0

    if ANCHOR not in text:
        raise SystemExit(
            "ERROR: could not find first worktree snapshot begin anchor in scripts/prove_ci.sh"
        )

    text = text.replace(ANCHOR, NEEDED + ANCHOR, 1)
    PROVE.write_text(text, encoding="utf-8")
    print("OK: added prove_ci root worktree snapshot init (v1)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
