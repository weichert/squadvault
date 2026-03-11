from __future__ import annotations

from pathlib import Path
import sys

PROVE = Path("scripts/prove_ci.sh")

ANCHOR = "bash scripts/gate_no_bare_chevron_markers_v1.sh"

MARKER = "# prove_ci_wire_patch_wrapper_idempotence_gate_v1"

INSERT = """\
{marker}
echo "==> Gate: patch wrapper idempotence (allowlist) v1"
bash scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

""".format(marker=MARKER)


def main() -> int:
    if not PROVE.exists():
        print(f"ERROR: missing canonical file: {PROVE}", file=sys.stderr)
        return 2

    original = PROVE.read_text(encoding="utf-8")

    if MARKER in original:
        return 0

    pos = original.find(ANCHOR)
    if pos == -1:
        print(f"ERROR: could not find anchor in {PROVE}: {ANCHOR!r}", file=sys.stderr)
        return 3

    line_end = original.find("\n", pos)
    if line_end == -1:
        line_end = len(original)

    updated = original[: line_end + 1] + "\n" + INSERT + original[line_end + 1 :]

    if updated == original:
        return 0

    PROVE.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
