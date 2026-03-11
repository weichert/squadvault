#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

NOTE_LINE = "# NOTE: BSD mktemp requires the template to end with XXXXXX (no suffix), so we omit .sqlite.\n"
SUCCESS_LINE = 'echo "OK: CI working tree remained clean (guardrail enforced)."\n'

INVARIANT_DOC_PATH = Path("docs/80_indices/ops/CI_Cleanliness_Invariant_v1.0.md")
INVARIANT_DOC = """# SquadVault — CI Cleanliness & Determinism Guardrail (v1.0)

Status: ACTIVE (enforced)

## Invariant

When running the authoritative CI proof entrypoint:

- **Entrypoint:** `scripts/prove_ci.sh`
- The git working tree **must remain clean** throughout the run.
- If the run begins dirty: **fail early**.
- If the run dirties the repo (tracked or untracked): **fail loudly** with an actionable diff summary.
- No silent cleanup of repo state. No masking.

## Rationale

Even with fixture immutability enforced, allowing proofs to dirty the working tree can:

- mask nondeterminism
- hide bugs that only appear from a clean checkout
- undermine auditability and operator trust

This guardrail prioritizes detect + fail over convenience.

## Enforcement

- Pre-check: `scripts/check_repo_cleanliness_ci.sh --phase before`
- Post-check (EXIT): `scripts/check_repo_cleanliness_ci.sh --phase after`

Any porcelain output is a hard failure.

## Recovery (operator choice)

- Inspect: `git status`
- Discard tracked changes: `git restore --staged --worktree -- .`
- Remove untracked (destructive): `git clean -fd`
"""

def die(msg: str) -> int:
    print(f"ERROR: {msg}")
    return 2

def main() -> int:
    prove = Path("scripts/prove_ci.sh")
    if not prove.exists():
        return die("missing scripts/prove_ci.sh")

    s = prove.read_text(encoding="utf-8")

    # --- A) Ensure BSD mktemp note sits immediately above WORK_DB mktemp line ---
    mktemp_line = 'WORK_DB="$(mktemp "${SV_TMPDIR}/squadvault_ci_workdb.XXXXXX")"\n'
    idx = s.find(mktemp_line)
    if idx == -1:
        return die("could not find expected WORK_DB mktemp line")

    # find line start of mktemp_line
    line_start = s.rfind("\n", 0, idx) + 1
    prev_block = s[max(0, line_start - 500):line_start]

    if NOTE_LINE not in prev_block:
        # Insert note directly above mktemp line
        s = s[:line_start] + NOTE_LINE + s[line_start:]

    # --- B) Add explicit success marker near the end ---
    # Anchor: the script already prints "OK: CI proof suite passed"
    anchor = 'echo "OK: CI proof suite passed"\n'
    aidx = s.find(anchor)
    if aidx == -1:
        return die('could not find anchor: echo "OK: CI proof suite passed"')

    after_anchor_pos = aidx + len(anchor)
    tail = s[after_anchor_pos:after_anchor_pos + 400]

    if SUCCESS_LINE not in tail:
        s = s[:after_anchor_pos] + SUCCESS_LINE + s[after_anchor_pos:]

    prove.write_text(s, encoding="utf-8", newline="\n")
    print("OK: patched scripts/prove_ci.sh (note + success marker).")

    # --- C) Write invariant doc (idempotent) ---
    # Create dirs if needed
    INVARIANT_DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    if INVARIANT_DOC_PATH.exists():
        # Don't overwrite if it exists; keep it stable.
        print(f"OK: invariant doc exists (no-op): {INVARIANT_DOC_PATH}")
    else:
        INVARIANT_DOC_PATH.write_text(INVARIANT_DOC, encoding="utf-8", newline="\n")
        print(f"OK: wrote invariant doc: {INVARIANT_DOC_PATH}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
