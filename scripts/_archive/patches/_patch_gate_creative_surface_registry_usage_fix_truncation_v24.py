from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

MARK = "SV_CSRU_EXTRACT_V24"
RX_DQ = '"CREATIVE_SURFACE_[A-Z0-9_]+"'  # ERE token; + needs -E

# Candidate line: grep + (-o or -Eo or -oE) + CREATIVE_SURFACE_ on same line; skip doc-marker greps
CAND = re.compile(r"\bgrep\b", re.IGNORECASE)
HAS_O = re.compile(r"\s-(?:E)?o\b|\s-oE\b", re.IGNORECASE)

# Replace any CREATIVE_SURFACE_* regex-ish chunk (quoted or unquoted) with RX_DQ
RE_QUOTED = re.compile(r"""(['"])([^'"]*CREATIVE_SURFACE_[^'"]*)\1""")
RE_BARE1 = re.compile(r"CREATIVE_SURFACE_\[[A-Za-z0-9_]+\]\+")
RE_BARE2 = re.compile(r"CREATIVE_SURFACE_[A-Za-z0-9_\\\{\}\[\]\+\*\?\(\)\|]+")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")
    if MARK in src:
        print(f"OK: {MARK} already present (noop)")
        return

    lines = src.splitlines(keepends=True)

    hits: list[int] = []
    for i, ln in enumerate(lines):
        if not CAND.search(ln):
            continue
        if "CREATIVE_SURFACE_" not in ln:
            continue
        if "SV_CREATIVE_SURFACE_REGISTRY_ENTRIES" in ln:
            continue
        if HAS_O.search(ln) is None:
            continue
        hits.append(i)

    if len(hits) != 1:
        raise SystemExit(
            "ERROR: expected exactly one grep extractor line with -o/-Eo/-oE and CREATIVE_SURFACE_.\n"
            f"Found {len(hits)} candidates: {hits}\n"
            "TIP: grep -n \"CREATIVE_SURFACE_\" scripts/gate_creative_surface_registry_usage_v1.sh | grep -E \"grep|-(E)?o\""
        )

    i = hits[0]
    ln = lines[i]

    # Ensure -Eo in a robust way (handles -oE, -o, -Eo)
    ln2 = ln
    # -oE -> -Eo
    ln2 = re.sub(r"(\s)-oE(\s)", r"\1-Eo\2", ln2, count=1, flags=re.IGNORECASE)
    # " -o " or " -Eo " -> force to -Eo
    ln2 = re.sub(r"(\s)-(?:E)?o(\s)", r"\1-Eo\2", ln2, count=1, flags=re.IGNORECASE)

    before = ln2

    # Prefer replacing a quoted regex chunk containing CREATIVE_SURFACE_
    ln2, n = RE_QUOTED.subn(RX_DQ, ln2, count=1)
    if n == 0:
        # Else replace common bare forms
        ln2, n1 = RE_BARE1.subn("CREATIVE_SURFACE_[A-Z0-9_]+", ln2, count=1)
        if n1 == 0:
            ln2, n2 = RE_BARE2.subn("CREATIVE_SURFACE_[A-Z0-9_]+", ln2, count=1)
            if n2 == 0:
                # Last resort: replace a simple token prefix if present
                ln2, n3 = re.subn(r"CREATIVE_SURFACE_[A-Za-z0-9_]+", "CREATIVE_SURFACE_[A-Z0-9_]+", ln2, count=1)
                if n3 == 0:
                    raise SystemExit(
                        "ERROR: found extractor line but could not locate a replaceable CREATIVE_SURFACE_* regex chunk on it.\n"
                        "TIP: open the line and patch manually, or share the line here."
                    )
        # If we replaced a bare form, quote it so '+' is treated as ERE reliably
        if "CREATIVE_SURFACE_[A-Z0-9_]+" in ln2 and '"' not in ln2 and "'" not in ln2:
            ln2 = ln2.replace("CREATIVE_SURFACE_[A-Z0-9_]+", RX_DQ.strip('"'), 1)
            ln2 = ln2.replace(RX_DQ.strip('"'), RX_DQ, 1)

    if "CREATIVE_SURFACE_" not in ln2:
        raise SystemExit("ERROR: internal: patch removed CREATIVE_SURFACE_ unexpectedly")

    lines[i] = ln2

    # Add marker near top (after shebang)
    insert_at = 1 if lines and lines[0].startswith("#!") else 0
    lines.insert(insert_at, f"# {MARK}: extractor regex is full-token + quote-safe\n")

    TARGET.write_text("".join(lines), encoding="utf-8")
    print("OK: v24 applied (extractor hardened; structure preserved; idempotent marker added)")

if __name__ == "__main__":
    main()
