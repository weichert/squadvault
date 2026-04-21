# Finding 2 — `gate_ci_guardrails_ops_entrypoints_section_v2.sh` failure classification

**Date:** 2026-04-22
**Session:** Diagnostic-only follow-up to
`OBSERVATIONS_2026_04_20_PRECOMMIT_GATE_PARITY_DEFERRED_FINDINGS.md`
Finding 2. Classify-before-fix per standing posture.
**Commit-of-record:** no commit this session — diagnostic only.
**HEAD at diagnosis:** `038e51a`.
**Capture:** `/tmp/finding2_stdout.txt`, `/tmp/finding2_trace.txt`.
**Status:** FINAL (classification). Fix deferred to a separately briefed
session.

---

## Classification

**Hypothesis (b) confirmed.** The bounded markers the gate enforces
were removed from `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` at
commit **`0faf0c0`** ("Phase 7.8 — CI Guardrail Registry Completeness
Lock", 2026-03-10) without retiring or updating the gate. The gate
has been failing at every HEAD since.

Hypothesis (a) — "CI-only behavior, different file layout" — is
disproven by reading the gate source. It does `test -f` on the index
path and `awk` over the file; no CI-vs-local branching exists.

Hypothesis (c) — "gate never satisfied at HEAD" — is disproven by the
diff of `c91ff50` ("CI/Docs: wire ops entrypoints TOC + enforce via
gate v2 (v3)", 2026-02-06), which introduced the gate and both
marker families **in the same commit**. The gate was satisfied at
its own introduction.

---

## Reproduction

At HEAD `038e51a`:

```
bash -x scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh \
  > /tmp/finding2_stdout.txt 2> /tmp/finding2_trace.txt
```

Exit code: `1`.

The `-x` trace shows:

1. `test -f docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` passes
   (the file exists).
2. The function `extract_bounded` is invoked for the TOC markers
   `<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->` /
   `<!-- SV_END: ops_entrypoints_toc (v1) -->`.
3. `awk` runs over the file and returns empty output (neither marker
   is present in the file).
4. The function's emptiness check fires, echoes the ERROR message, and
   calls `exit 1`.
5. The script aborts at that point. The `ops_entrypoints_hub` section
   check and the grep chain never execute.

A broad grep of the live tree (excluding `.git`, `_archive`,
`_graveyard`, `_retired`) confirms neither marker family is present in
any live source of truth at HEAD:

```
SV_BEGIN: ops_entrypoints_toc  → only in the gate + this memo's predecessor
SV_BEGIN: ops_entrypoints_hub  → only in the gate
```

---

## Archaeology

### Gate introduction — `c91ff50`, 2026-02-06

Single commit introduced:

- `scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh` (+53 lines).
- A `.py` sibling of the same gate (+88 lines).
- `patch_ci_guardrails_add_ops_entrypoints_toc_v1` (.py + .sh).
- `prove_ci_add_ci_guardrails_ops_entrypoints_gate_v3` (.py + .sh).
- `+4` lines to `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`
  inserting the TOC markers around the `[Ops Entrypoints (Canonical)]`
  anchor.

The `ops_entrypoints_hub` markers had already been inserted by an
earlier commit, `93f8e16` ("CI/Docs: enforce CI Guardrails canonical
ops entrypoints section (v1)"). That commit is unrelated to this
session; mentioned only to locate the other marker family in history.

At `c91ff50`, the gate was satisfied.

### Gate began failing — `0faf0c0`, 2026-03-10

`Phase 7.8 — CI Guardrail Registry Completeness Lock` rewrote the
index file `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` from
**219 lines down to a condensed version** retaining only the "CI
Guardrails Ops Entrypoints" registry block (the
`SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN`/`_END` block).

Everything else was deleted. In particular:

- The `## Contents` TOC section containing the
  `<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->` /
  `<!-- SV_END: ops_entrypoints_toc (v1) -->` markers around the
  `[Ops Entrypoints (Canonical)](#ops-entrypoints-canonical)` anchor.
- The `<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->` /
  `<!-- SV_END: ops_entrypoints_hub (v1) -->` prose section listing
  the six canonical hub doc links the gate's grep chain checks for.

The commit message is a one-liner with no description. Intent cannot
be inferred from the record alone (silence over speculation).

### Since `0faf0c0`

No commit has touched either marker family in the index. `git log -G`
on the exact marker strings returns only `c91ff50` and `0faf0c0` for
the TOC family, and `93f8e16` and `0faf0c0` for the hub family. The
gate has been failing continuously for ~6 weeks.

---

## Process findings surfaced during diagnosis

These are **adjacent observations** that came into view while
classifying Finding 2. Each is worth recording but neither is in scope
for the Finding 2 fix.

### A. Gate is registered in the Entrypoints Registry but its target is gone

At HEAD, `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` line 12 still
reads:

    - scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh — CI Guardrails ops entrypoints section + TOC (v2)

The gate is declared as an active guardrail in the registry surface
that's enforced by `gate_ci_guardrails_registry_completeness_v1.sh`,
`gate_ci_guardrails_registry_authority_v1.sh`, and
`gate_ci_guardrails_surface_freeze_v1.sh` — all of which pass. So the
gate is "registered" as authoritative. But the content it's meant to
enforce (the marker blocks) has been removed. The registry-level
enforcement is consistent (the gate is listed), and the gate-level
enforcement is broken (its check target is gone) — each system is
internally consistent, and the contradiction is between them.

### B. `prove_ci.sh` does not use `set -e`

`scripts/prove_ci.sh` is 358 lines and invokes roughly 100 gates and
proofs in sequence. It does **not** set `-e`, `-u`, or `-o pipefail`.
The only occurrences of `set` in the file are two `|| true` fallbacks
on cleanup commands. Each gate is invoked as a bare line:

    bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh

Without errexit, a failing gate does not abort the script. Because GH
Actions' `run: bash scripts/prove_ci.sh` step propagates the script's
final exit code, and `prove_ci.sh`'s final exit code is the rc of its
last command (the worktree-cleanliness end-snapshot check),
**failures in any gate invoked before the last line are silently
absorbed at the CI level.**

This is sufficient explanation for why Finding 2 has been "silent red"
for six weeks. CI has been green for other reasons (most gates pass,
and the final worktree-cleanliness check passes), and the failure of
this particular gate has been invisible to the CI outcome.

Whether the absence of errexit is deliberate (e.g., to surface all
failures in one run) or accidental is not determinable from the
source. The file has no comment explaining the choice, and no
post-processor aggregating per-gate exit codes is visible. This is
an observation, not an assertion of defect.

**Scope of this finding:** this pattern applies to every gate invoked
by `prove_ci.sh`, not just the one under diagnosis. Any other gate
that starts failing is subject to the same invisibility in CI.

### C. Gate failure reporting swallows its own ERROR message

Secondary observation on the gate's own stdout discipline. In
`extract_bounded`, when the awk extraction returns empty:

    out="$(awk ...)"
    if [[ -z "${out}" ]]; then
      echo "ERROR: missing bounded section in ${DOC}"
      echo "  begin=${begin}"
      echo "  end=${end}"
      exit 1
    fi

The caller captures the function's stdout via command substitution:

    toc="$(extract_bounded "${BEGIN_TOC}" "${END_TOC}")"

So the three ERROR lines echoed by `extract_bounded` are written to
the function's stdout, which is captured into `$toc` — never reaching
the user's terminal. To a human running the gate, only the header
banner appears on stdout before `rc=1`. The informative diagnostic is
silently absorbed.

This doesn't affect the classification of Finding 2, but it did
mislead this diagnostic session by ~one turn (an initial reproduction
using `$?` after a pipeline also captured the wrong rc, which
compounded the confusion). A future fix pass might want to route
error output to stderr in `extract_bounded`.

---

## What this session does not do

- Does not change the gate.
- Does not change the index file.
- Does not re-add the deleted marker families.
- Does not retire the gate.
- Does not change `prove_ci.sh`.
- Does not change the GH Actions workflow.
- Does not assert intent for commit `0faf0c0`.

---

## Options for the fix pass (next session)

Three legitimate shapes for the actual fix. No recommendation here —
the next session's brief makes the decision.

### Option 1: Re-introduce the markers

Restore the deleted marker blocks to
`docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`. The gate starts
passing. Requires deciding whether the prose content inside the hub
marker block (six canonical doc links) and the TOC anchor entry are
still canonical. If `0faf0c0` intentionally narrowed the index to the
entrypoints registry only, re-adding the hub prose reverses that
decision. Archaeology on `0faf0c0`'s intent (commit message, nearby
memos, Phase 7.8 spec if one exists) would inform this path.

### Option 2: Retire the gate

Remove `scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh`,
remove its line from `prove_ci.sh`, remove its entry from the
Entrypoints Registry at `CI_Guardrails_Index_v1.0.md:12`. Archive the
gate per standard pattern. The registry is internally consistent, CI
turns measurably cleaner (rc=1 source removed), and the `ops
entrypoints section + TOC` concept is dropped from the enforced
surface. Requires confirming nothing the gate was guarding is worth
preserving under a different mechanism.

### Option 3: Rewrite the gate to match the current index shape

Rewrite the gate to enforce whatever invariants the current
(post-`0faf0c0`) index is intended to guarantee. This is a
heavier lift: it requires knowing what the current index *is* meant
to enforce, which is another archaeology question about Phase 7.8's
intent.

Orthogonal to all three: **Finding B (prove_ci.sh lacks errexit) is
its own session** and should not be bundled with the Finding 2 fix.
That change has a much wider blast radius and warrants its own brief.

---

## Recommended posture for the next session

Before picking Options 1/2/3, spend ~15 minutes on the archaeology
question about commit `0faf0c0`:

- Is there a Phase 7.8 spec or memo?
- Does `CI_MILESTONES.md` or any index describe what Phase 7.8 did?
- Is there a pattern in nearby commits (Phase 7.7, 7.8, 7.9) that
  suggests the narrowing of the index was deliberate?

The archaeology answer likely resolves the Options 1 vs 2 vs 3
question directly. If the narrowing was deliberate, Option 2 (retire)
is indicated. If it was accidental, Option 1 (restore) is indicated.
Option 3 is a fallback when neither is clean.

---

## Carry-forward

- Finding 2 (this one) → classified. Ready for a fix-pass session.
- Finding B (`prove_ci.sh` lacks errexit) → new. Separately briefable.
  Scope: all ~100 gates, not just this one.
- Finding C (gate swallows own ERROR via command-substitution capture)
  → new. Minor. Could be bundled with whichever gate rewrite or
  hygiene pass picks it up.
- Standing backlog items from the hook-installer session memo remain
  untouched.
