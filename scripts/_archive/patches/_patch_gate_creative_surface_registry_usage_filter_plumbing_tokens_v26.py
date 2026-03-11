from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

MARK = "SV_CSRU_FILTER_PLUMBING_V26"
FILTER = r"sed -E '/^(CREATIVE_SURFACE_REGISTRY_ENTRIES|CREATIVE_SURFACE_REGISTRY_ENTRY)(_|$)/d'"

CAND = re.compile(r"\bgrep\b", re.IGNORECASE)
HAS_O = re.compile(r"\s-(?:E)?o\b|\s-oE\b", re.IGNORECASE)

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")
    if MARK in src or FILTER in src:
        print(f"OK: {MARK} already present (noop)")
        return

    lines = src.splitlines(keepends=True)

    hits: list[int] = []
    for i, ln in enumerate(lines):
        if "SV_CREATIVE_SURFACE_REGISTRY_ENTRIES" in ln:
            continue
        if "CREATIVE_SURFACE_" not in ln:
            continue
        if not CAND.search(ln):
            continue
        if HAS_O.search(ln) is None:
            continue
        hits.append(i)

    if len(hits) != 1:
        raise SystemExit(
            "ERROR: expected exactly one grep extractor line with -o/-Eo/-oE and CREATIVE_SURFACE_.\n"
            f"Found {len(hits)} candidates: {hits}\n"
            "TIP: grep -n \"CREATIVE_SURFACE_\" scripts/gate_creative_surface_registry_usage_v1.sh | grep -E \"-(E)?o|-oE\""
        )

    i = hits[0]
    ln = lines[i]

    # Case A: command substitution closes on this line: ... $( ... )
    # Inject ` | FILTER` immediately before final ')'
    if re.search(r"\)\s*$", ln) and "$(" in ln:
        ln2 = re.sub(r"\)\s*$", f" | {FILTER})\n", ln.rstrip("\n") + "\n", count=1)
    else:
        # Case B: not a $(...) one-liner -> append a pipeline stage safely
        ln2 = ln.rstrip("\n") + f" | {FILTER}\n"

    lines[i] = ln2

    # Marker near top (after shebang)
    insert_at = 1 if lines and lines[0].startswith("#!") else 0
    lines.insert(insert_at, f"# {MARK}: drop plumbing tokens from extracted CREATIVE_SURFACE_* refs\n")

    TARGET.write_text("".join(lines), encoding="utf-8")
    print("OK: v26 applied (plumbing tokens filtered from refs set; non-pipeline safe)")

if __name__ == "__main__":
    main()
