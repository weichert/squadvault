from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

MARK = "SV_CSRU_V29_CANONICAL_EXTRACTOR_AND_STRAY_DOC_LINE"

REG_DOC = "docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"

# Plumbing prefixes forbidden by the test
PLUMBING_SED = r"sed -E '/^(CREATIVE_SURFACE_REGISTRY_ENTRIES|CREATIVE_SURFACE_REGISTRY_ENTRY)(_|$)/d'"

# Canonical token extractor (no quotes in match; ERE)
TOKEN_GREP = "grep -Eo 'CREATIVE_SURFACE_[A-Z0-9_]+'"

# Find the one line that extracts referenced CREATIVE_SURFACE_* tokens.
# We expect exactly one such "grep ... -o/-Eo ... CREATIVE_SURFACE_" line.
CAND = re.compile(r"\bgrep\b.*\s-(?:E)?o\b.*CREATIVE_SURFACE_", re.IGNORECASE)

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src0 = TARGET.read_text(encoding="utf-8")
    if MARK in src0:
        print(f"OK: {MARK} already present (noop)")
        return

    lines = src0.splitlines(keepends=True)
    out: list[str] = []
    changed = 0

    # (A) Remove any standalone line that tries to execute the registry doc path
    #     (this is exactly what yields "Permission denied" on that md file)
    # Also remove stray git-pathspec forms like :!**/docs/...md sitting alone.
    stray_doc_line = re.compile(r"^\s*(?::!\*{0,2}/?)?" + re.escape(REG_DOC) + r"\s*$")

    # (B) Rewrite the extractor line into a canonical pipeline:
    #     ... | grep -Eo 'CREATIVE_SURFACE_[A-Z0-9_]+' | sed -E '/^(...)/d'
    # We preserve the *rest* of the line (prefix/suffix), only replacing the grep segment + ensuring a pipeline.
    hit_idxs: list[int] = []
    for i, ln in enumerate(lines):
        if stray_doc_line.match(ln):
            changed += 1
            continue
        out.append(ln)

    # Find candidates AFTER stray removal
    hits = []
    for i, ln in enumerate(out):
        if "SV_CREATIVE_SURFACE_REGISTRY_ENTRIES" in ln:
            continue
        if CAND.search(ln):
            hits.append(i)

    if len(hits) != 1:
        raise SystemExit(
            "ERROR: expected exactly one extractor line with grep -o/-Eo and CREATIVE_SURFACE_.\n"
            f"Found {len(hits)} candidates: {hits}\n"
            "TIP: grep -n \"CREATIVE_SURFACE_\" scripts/gate_creative_surface_registry_usage_v1.sh | grep -E \"-(E)?o\""
        )

    i = hits[0]
    ln = out[i]

    # Strategy: replace the grep invocation portion with our canonical grep, and ensure plumbing filter is applied.
    # We avoid breaking $(...) by injecting inside it if present.
    #
    # Cases we handle:
    #   1) line contains $( ... ) on this line: inject " | TOKEN_GREP | PLUMBING_SED" before final ')'
    #   2) otherwise: ensure the line becomes a pipeline by appending " | TOKEN_GREP | PLUMBING_SED"
    #
    # First, remove any existing grep -o/-Eo token extractor (to avoid double-grep).
    # We only remove one grep...CREATIVE_SURFACE... token-ish argument chunk.
    ln2 = ln

    # Remove existing grep -o/-Eo ... CREATIVE_SURFACE_... (best-effort, single pass)
    ln2, n_rm = re.subn(
        r"""\bgrep\b[^\n|;]*\s-(?:E)?o\b[^\n|;]*CREATIVE_SURFACE_[^\n|;]*""",
        "",
        ln2,
        count=1,
        flags=re.IGNORECASE,
    )
    if n_rm:
        changed += 1

    # Normalize any accidental "||" / "|  |" introduced by removal
    ln2 = re.sub(r"\|\s*\|", "|", ln2)
    ln2 = re.sub(r"\|\s*$", "", ln2.rstrip("\n")) + ("\n" if ln2.endswith("\n") else "")

    # Now inject canonical stages
    if "$(" in ln and re.search(r"\)\s*$", ln.strip()):
        # Inject before the final ')'
        ln2 = re.sub(r"\)\s*$", f" | {TOKEN_GREP} | {PLUMBING_SED})", ln2.rstrip("\n"), count=1) + "\n"
        changed += 1
    else:
        # Append as a pipeline (keeps structure; bash -n safe)
        ln2 = ln2.rstrip("\n") + f" | {TOKEN_GREP} | {PLUMBING_SED}\n"
        changed += 1

    out[i] = ln2

    # Add marker after shebang
    insert_at = 1 if out and out[0].startswith("#!") else 0
    out.insert(insert_at, f"# {MARK}: canonical token extractor + filter plumbing + drop stray doc line\n")

    TARGET.write_text("".join(out), encoding="utf-8")
    print(f"OK: v29 applied (changed_lines={changed})")

if __name__ == "__main__":
    main()
