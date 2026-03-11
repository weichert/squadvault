from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

MARKER = "<!-- SV_CI_REGISTRY_EXECUTION_ALIGNMENT: v1 -->"
BULLET = "- scripts/gate_ci_registry_execution_alignment_v1.sh — CI Registry → Execution Alignment Gate (v1)"

# Canonical anchor: place immediately after the existing proof surface registry marker block.
# This keeps the Ops index “registry-related gates” clustered and discoverable.
ANCHOR = "<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"ERROR: missing index: {INDEX}")

    text = INDEX.read_text(encoding="utf-8")

    if ANCHOR not in text:
        raise SystemExit(
            "ERROR: canonical anchor not found in Ops index (fail-closed):\n"
            f"  expected: {ANCHOR}\n"
            "Refusing to guess insertion point."
        )

    # Idempotence: if our marker already exists, ensure the bullet exists exactly once.
    if MARKER in text:
        # Ensure bullet present under marker (very small, deterministic repair).
        parts = text.split(MARKER, 1)
        pre = parts[0] + MARKER
        rest = parts[1]

        # Insert bullet right after marker line if not present anywhere.
        if BULLET not in rest:
            # Put bullet on the next line after marker.
            if rest.startswith("\n"):
                rest = rest[1:]
            new = pre + "\n" + BULLET + "\n" + rest
            INDEX.write_text(new, encoding="utf-8")
        return

    lines = text.splitlines(True)
    out: list[str] = []

    inserted = False
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        if (not inserted) and (ANCHOR in line):
            # After ANCHOR, there should be a bullet line right after (by convention).
            # We insert our marker+bullett immediately AFTER the anchor block’s bullet line,
            # i.e., after the next line that begins with "- " (or immediately if not found).
            j = i + 1
            if j < len(lines) and lines[j].lstrip().startswith("- "):
                out.append(lines[j])
                i = j
            out.append(MARKER + "\n")
            out.append(BULLET + "\n")
            inserted = True

        i += 1

    if not inserted:
        raise SystemExit("ERROR: failed to insert Ops index entry (unexpected)")

    INDEX.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
