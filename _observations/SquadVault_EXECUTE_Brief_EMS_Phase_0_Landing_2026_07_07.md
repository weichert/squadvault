# EXECUTE Brief — EMS Phase 0 Preservation Landing (2026-07-07)

**Lane:** EXECUTE (Claude Code, fresh session)
**Authored by:** DECIDE session 2026-07-07, founder-ratified
**Precondition:** This brief must be on main before the fresh session that runs it, per
standing convention. Founder lands the brief via the standard paste flow first.

## Scope

Land two files on the engine repo main:

1. `_observations/OBSERVATIONS_2026_07_07_EMS_PHASE_0_PRESERVATION.md`
2. The Environmental Memory founder vision draft (markdown conversion),
   `Environmental_Memory_Founder_Draft_v0_9.md`

One topic, one commit: EMS Phase 0 preservation. No source code, schema, route, seed, or
frontend changes are in scope. This is a documentation-only landing.

## Steps

**Step 1 — Clone and verify identity.**
Fresh clone of `weichert/squadvault`. Confirm engine repo with the discriminator:
`test -f scripts/recap_artifact_regenerate.py` must succeed. Verify HEAD and record the
commit hash in the session log. If the discriminator fails, halt — wrong repo.

**Step 2 — Place the memo.**
Copy `OBSERVATIONS_2026_07_07_EMS_PHASE_0_PRESERVATION.md` into `_observations/`. Never at
repo root (root allowlist test enforces exactly 5 root files).

**Step 3 — Place the vision draft. ⛔ FOUNDER GATE if ambiguous.**
Determine the correct home for a Tier-5-class non-binding vision document by inspecting the
repo at HEAD against the Canonical Folder Map. If a clear vision/docs location exists, place
`Environmental_Memory_Founder_Draft_v0_9.md` there. If no unambiguous location exists at
HEAD, do NOT guess and do NOT default to repo root or `_observations/` — halt and present the
candidate locations to the founder for a ruling. Escalate, never repair.

**Step 4 — Gates (separate paste turn from commit).**
Run the standard gates (ruff / mypy / pytest via `./scripts/py` shim and `prove_ci.sh` as
applicable). The root allowlist test must pass. Gates and git commands are never chained in
one paste turn.

**Step 5 — Commit (separate paste turn).**
Stage the two files explicitly by path (`git add <file> <file>`, never `-A`). Commit message
via `python3` heredoc writing `/tmp/msg.txt` with `pathlib.Path.write_text()`, then
`git commit -F /tmp/msg.txt`. ASCII subject, no Co-Authored-By trailers. Suggested subject:

    Land EMS Phase 0 preservation memo and founder vision draft

Body should reference the memo filename and note documentation-only scope.

**Step 6 — PR and merge. ⛔ FOUNDER GATE before merge.**
Push branch, open PR, present the diff summary to the founder. On approval, merge via
`gh pr merge --squash` CLI only (never the browser button). Verify on a fresh main pull that
both files are present at their landed paths and HEAD matches the merge.

## Verification checklist (post-merge)

- [ ] `_observations/OBSERVATIONS_2026_07_07_EMS_PHASE_0_PRESERVATION.md` present on main
- [ ] Vision draft present at the founder-ruled location
- [ ] Root allowlist test green on main
- [ ] No files outside the two in-scope paths changed

## Out of scope (do not do)

- No hook implementation (H1–H4 are discipline constraints, not work items)
- No checklist amendment drafting (Phase 1)
- No schema, route, seed, or frontend changes
- No STATE.md phase changes unless the founder rules that Phase 0 registration belongs there;
  if STATE.md convention at HEAD indicates roadmap-candidate registration is recorded in
  STATE.md, present that as a question at the Step 6 gate rather than editing unprompted.
