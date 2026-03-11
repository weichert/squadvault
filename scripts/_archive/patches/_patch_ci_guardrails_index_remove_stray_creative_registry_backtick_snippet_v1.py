from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CREATIVE_SURFACE_REGISTRY_DISCOVERABILITY_v1_BEGIN -->"
END = "<!-- SV_CREATIVE_SURFACE_REGISTRY_DISCOVERABILITY_v1_END -->"

# Exact stray line fragment observed in your grep output:
SNIPPET = "`docs/80_indices/ops/Creative_Surface_Registry_v1.0.md`"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"Refusing: missing {INDEX}")

    txt = INDEX.read_text(encoding="utf-8")

    if (BEGIN in txt) != (END in txt):
        raise SystemExit("Refusing: discoverability block markers are partial (BEGIN/END mismatch).")

    lines = txt.splitlines(True)
    out: list[str] = []
    in_block = False
    removed = 0

    for ln in lines:
        if BEGIN in ln:
            in_block = True
        if END in ln:
            out.append(ln)
            in_block = False
            continue

        if in_block:
            out.append(ln)
            continue

        if SNIPPET in ln:
            removed += 1
            continue

        out.append(ln)

    if removed == 0:
        return

    INDEX.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
