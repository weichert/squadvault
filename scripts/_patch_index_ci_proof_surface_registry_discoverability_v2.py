from __future__ import annotations

from pathlib import Path
import sys

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

MARKER = "<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->"
BULLET = "- scripts/check_ci_proof_surface_matches_registry_v1.sh — CI Proof Surface Registry Gate (canonical)"

BLOCK = MARKER + "\n" + BULLET + "\n\n"


def main() -> int:
    if not INDEX.exists():
        print(f"ERROR: missing index file: {INDEX}", file=sys.stderr)
        return 2

    original = INDEX.read_text(encoding="utf-8")

    # Line-based exact removal; preserve all other content ordering.
    lines = original.splitlines()
    filtered: list[str] = []
    for line in lines:
        if line == MARKER:
            continue
        if line == BULLET:
            continue
        filtered.append(line)

    # CRITICAL for idempotence: remove trailing blank lines left behind by prior block(s).
    while filtered and filtered[-1] == "":
        filtered.pop()

    rebuilt = "\n".join(filtered)
    if rebuilt != "":
        rebuilt += "\n"
    rebuilt += BLOCK

    if rebuilt == original:
        return 0

    INDEX.write_text(rebuilt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
