from __future__ import annotations

from pathlib import Path
import sys

PROVE = Path("scripts/prove_ci.sh")

ANCHOR = "# ==> Gate: CI proof surface registry (v1)"

INSERT_BLOCK = """\
echo "==> Gate: CI proof surface registry discoverability in Ops index (v1)"
bash scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh

"""

MARKER = "# prove_ci_wire_ci_proof_surface_registry_index_discoverability_gate_v3"


def main() -> int:
    if not PROVE.exists():
        print(f"ERROR: missing canonical file: {PROVE}", file=sys.stderr)
        return 2

    original = PROVE.read_text(encoding="utf-8")

    # Idempotence: if already wired, no-op.
    if MARKER in original:
        return 0

    pos = original.find(ANCHOR)
    if pos == -1:
        print(
            f"ERROR: could not find anchor line in {PROVE}: {ANCHOR!r}",
            file=sys.stderr,
        )
        return 3

    # Insert immediately after the anchor line (end of that line).
    line_end = original.find("\n", pos)
    if line_end == -1:
        line_end = len(original)

    insertion = "\n" + MARKER + "\n" + INSERT_BLOCK
    updated = original[: line_end + 1] + insertion + original[line_end + 1 :]

    if updated == original:
        return 0

    PROVE.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
