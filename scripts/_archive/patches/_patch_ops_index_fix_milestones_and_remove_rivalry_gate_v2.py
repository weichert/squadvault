from __future__ import annotations

from pathlib import Path
import glob
import re
import sys

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

NEEDLE_RIVALRY = "scripts/gate_rivalry_chronicle_output_contract_v1.sh"
DESC_MILESTONES = "Enforce CI_MILESTONES.md has exactly one bounded ## Latest block (v1)"
DESC_RIVALRY = "Enforce Rivalry Chronicle export conforms to output contract (v1)"

# Robust content signals for the CI_MILESTONES "Latest bounded block" gate.
# We score candidates by how many signals appear in the script text (case-insensitive).
SIGNALS = (
    "CI_MILESTONES",      # usually present in file path / grep
    "CI_MILESTONES.md",   # sometimes present
    "## Latest",          # gate intent
    "bounded",            # bounded block logic
    "Latest",             # fallback
    "Milestone",          # fallback
)

def _score(txt: str) -> int:
    t = txt.lower()
    score = 0
    for s in SIGNALS:
        if s.lower() in t:
            score += 1
    return score

def _discover_milestones_gate_path() -> str | None:
    best_path: str | None = None
    best_score = 0
    candidates: list[tuple[int, str]] = []

    for p in sorted(glob.glob("scripts/gate_*.sh")):
        try:
            txt = Path(p).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        sc = _score(txt)
        if sc:
            candidates.append((sc, p))
        if sc > best_score:
            best_score = sc
            best_path = p

    # Require a minimally strong match to avoid misbinding.
    # We expect at least CI_MILESTONES + Latest/bounded to appear (>=2).
    if best_score >= 2:
        return best_path

    # If nothing meets threshold, refuse with helpful diagnostics (but still deterministic).
    if candidates:
        top = sorted(candidates, reverse=True)[:10]
        print("ERROR: could not confidently discover milestones gate (scores too low).", file=sys.stderr)
        print("Top candidates:", file=sys.stderr)
        for sc, p in top:
            print(f"  score={sc} path={p}", file=sys.stderr)
        return None

    print("ERROR: could not discover milestones gate (no scripts/gate_*.sh matched any CI_MILESTONES signals).", file=sys.stderr)
    return None

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing doc: {DOC}", file=sys.stderr)
        return 2

    milestones_gate = _discover_milestones_gate_path()
    if milestones_gate is None:
        return 3

    src = DOC.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    changed = False
    out: list[str] = []

    for ln in lines:
        # Remove rivalry export gate bullet.
        if (NEEDLE_RIVALRY in ln) and (DESC_RIVALRY in ln):
            changed = True
            continue

        # Fix miswired milestones bullet (keep description; swap script path).
        if (NEEDLE_RIVALRY in ln) and (DESC_MILESTONES in ln):
            new_ln = ln.replace(NEEDLE_RIVALRY, milestones_gate, 1)
            if new_ln != ln:
                changed = True
            out.append(new_ln)
            continue

        out.append(ln)

    if not changed:
        return 0

    DOC.write_text("".join(out), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
