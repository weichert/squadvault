from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN_RE = re.compile(r"^\s*<!--\s*SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN\s*-->\s*$")
END_RE = re.compile(r"^\s*<!--\s*SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END\s*-->\s*$")

TARGET_PATH = "scripts/gate_ci_proof_runners_block_sorted_v1.sh"
CANONICAL_DESC = (
    "Enforce CI_Proof_Surface_Registry CI_PROOF_RUNNERS block bullet ordering (v1)"
)

BULLET_RE = re.compile(r"^(\s*-\s*)(" + re.escape(TARGET_PATH) + r")(\s*—\s*)(.*)$")


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)

    begin_i = None
    end_i = None

    for i, line in enumerate(lines):
        if begin_i is None and BEGIN_RE.match(line):
            begin_i = i
            continue
        if begin_i is not None and END_RE.match(line):
            end_i = i
            break

    if begin_i is None or end_i is None or begin_i >= end_i:
        print("ERROR: could not locate bounded SV_CI_GUARDRAILS_ENTRYPOINTS_v1 block.", file=sys.stderr)
        return 3

    changed = False
    for i in range(begin_i + 1, end_i):
        m = BULLET_RE.match(lines[i].rstrip("\n"))
        if not m:
            continue

        prefix = m.group(1)
        path = m.group(2)
        dash = m.group(3)
        desc = m.group(4)

        if desc == CANONICAL_DESC:
            return 0  # already canonical

        lines[i] = f"{prefix}{path}{dash}{CANONICAL_DESC}\n"
        changed = True
        break

    if not changed:
        print("ERROR: target bullet not found inside entrypoints block.", file=sys.stderr)
        return 4

    TARGET.write_text("".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
