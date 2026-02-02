from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

EXPORT_PREFIX = "export SQUADVAULT_TEST_DB="
INSERT_LINE = 'export SQUADVAULT_TEST_DB="${WORK_DB}"\n'

ANCHOR = "# --- /Fixture DB working copy ---"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)

    export_idxs = [i for i, ln in enumerate(lines) if ln.strip().startswith(EXPORT_PREFIX)]
    if len(export_idxs) != 1:
        die(f"expected exactly 1 SQUADVAULT_TEST_DB export line; found {len(export_idxs)}")

    anchor_idxs = [i for i, ln in enumerate(lines) if ln.strip() == ANCHOR]
    if len(anchor_idxs) != 1:
        die(f'expected exactly 1 anchor line "{ANCHOR}"; found {len(anchor_idxs)}')

    export_idx = export_idxs[0]
    anchor_idx = anchor_idxs[0]

    lines.pop(export_idx)
    if anchor_idx > export_idx:
        anchor_idx -= 1

    if any(ln == INSERT_LINE for ln in lines):
        die("target insert export line already present; refusing (would duplicate)")

    lines.insert(anchor_idx + 1, INSERT_LINE)

    TARGET.write_text("".join(lines), encoding="utf-8")
    print("OK: moved SQUADVAULT_TEST_DB export to after WORK_DB finalized (v3)")


if __name__ == "__main__":
    main()
