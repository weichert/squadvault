# SESSION BRIEF - Unit E1.3: Doc/runbook hygiene sweep (engine side)

**Authored against engine HEAD `c05c49e`** (verify per charter section 3 before proceeding).
**Tool/model:** Claude Code / Opus 4.8. **Doc-only:** skips prove_ci; runs the four
pre-commit gates (banner, xtrace, repo-root allowlist, docs-Map) + the new ruff gate (E1.2).
**Source:** Document of Record v2.1 Unit E1.3 = Completion Plan v1.0 Unit 1.3.

## Founder adjudications (pre-decided - do not re-litigate)

- **Scope split:** this engine session covers ONLY engine-side items (runbook fix,
  Document of Record filing, charter amendment, DRAFTING the chat prompt). Frontend
  items (ROADMAP/SETUP/README in `~/squadvault`) are a SEPARATE session - author a
  session_brief for it in close-out. Sibling-clone deletion is a founder terminal action.
- **Document of Record now in scope:** file it in-repo, register in the docs Map, make
  "Document of Record readable in-repo" an acceptance criterion.
- **Charter amendment approved:** update CLAUDE.md "Product plan of record" pointer to the
  new in-repo path; log in section 9 as v1.0 -> v1.0.1, founder-approved 2026-06-09.

## VERIFICATION FINDINGS (git wins over brief - charter section 3.4)

1. **Runbook DB-path fix is ALREADY DONE - this work item is a NO-OP.**
   `docs/runbooks/distribution_v1.md` already uses `.local_squadvault.sqlite` (lines 27,
   38); zero `data/squadvault.db` occurrences remain. Fixed at `215cb39` ("docs: fix
   runbook DB path drift (F2 from Track A shipping memo)"). The Document of Record v2.1
   and Completion Plan still list it as a standing item because they pre-date / did not
   track `215cb39`. **Action: none** beyond recording it discharged. The remaining
   `data/squadvault.db` strings in the repo are historical references inside
   `_observations/` memos (immutable; do not edit).

2. **The Document of Record is NOT in the repo - BLOCKER for filing + amendment.**
   Adjudication says "I have copied it to docs/", but it is absent: not tracked, not
   untracked, not under any name; not in `~/projects/squadvault-ingest`, `~/squadvault`,
   `~/Downloads`, or `~/Desktop` either. **The file must be placed in the repo before the
   filing item (and the dependent charter-pointer update) can execute.** See "Blocked"
   below.

## Scope of work (engine session)

**A. Runbook DB-path fix** - VERIFIED ALREADY DONE (`215cb39`). No edit. Record discharged.

**B. File the Document of Record** - BLOCKED pending file placement (finding 2). Once the
file is in the repo:
- Place/rename to `docs/SquadVault_Product_Document_of_Record_v2_1.md` (contents are v2.1
  even though the founder's download is named v2_0).
- Register in the docs Map via a dated addendum `docs/map_patch_2026_06_09_document_of_record.md`
  (same precedent as STATE.md's `map_patch_2026_06_09_state_ledger.md`), satisfying the
  docs-Map registration gate.
- Add to `_GRANDFATHERED_TOP_LEVEL_DOCS` in `Tests/test_docs_map_registration_gate_v1.py`
  (the addendum AND the DoR file - both are new top-level docs/ files; the suite test is
  a separate surface from the gate, per the E1.1/STATE.md lesson).

**C. Charter amendment** (depends on B) - in `CLAUDE.md`:
- Line 14: `**Product plan of record:** \`SquadVault_Product_Document_of_Record_v2_0.md\`
  (v2.1).` -> point to `docs/SquadVault_Product_Document_of_Record_v2_1.md`.
- Section 9: append `- v1.0.1 - 2026-06-09 - Product-plan-of-record pointer updated to the
  in-repo path docs/SquadVault_Product_Document_of_Record_v2_1.md. Founder-approved.`
- NOTE: CLAUDE.md is the charter (Tier-4-adjacent) and is in the repo-root allowlist
  already (E1.1, `d119e6e`); editing it touches no allowlist count.

**D. Draft the chat project prompt** (independent; can run now) - draft TEXT only, output
in close-out for the founder to apply in claude.ai. Per the entry: current HEADs, Phase 11
status, shipped-surface list, the discharged-items table (from Document of Record Part 1).
Keep it SHORT - anchor, do not narrate. Pull current state from `git log` + STATE.md.

**E. Frontend session_brief** (close-out deliverable) - author
`_observations/session_brief_frontend_doc_sweep.md` for the `~/squadvault` session:
rewrite ROADMAP.md current-position + open-work against the frontend HEAD (`4e44bb3` per
the entry - re-verify in that repo, not this one), refresh SETUP.md, replace boilerplate
README.md. That session runs in `~/squadvault`, not here.

**F. Sibling-clone deletion** (close-out reminder) - remind founder to delete the stale
`~/projects/squadvault-ingest/` (their terminal action; not an engine commit).

## Acceptance criteria (binary)

1. `docs/SquadVault_Product_Document_of_Record_v2_1.md` exists, is tracked, and is readable
   in-repo; registered in the docs Map (addendum staged same commit); suite green.
2. CLAUDE.md pointer line resolves to the in-repo path; section 9 logs v1.0.1.
3. Runbook DB-path item recorded discharged (`215cb39`) - no new edit.
4. Chat project prompt draft delivered in close-out (text, for founder to apply).
5. Frontend session_brief authored in `_observations/`.
6. Doc-only gates green (banner/xtrace/allowlist/docs-Map/ruff); prove_ci SKIPPED per the
   doc-only path. STATE.md discharges E1.3; observation memo filed.

## BLOCKED - founder action required before execution

Place the Document of Record file into the repo (e.g. `docs/`), any filename - the session
will rename/register it. Until then, items B and C cannot execute; A/D/E/F can proceed but
the unit is not closeable. Recommend: founder drops the file, then "execute E1.3".

## OUT OF SCOPE

Frontend repo edits (separate session); sibling-clone deletion (founder terminal); applying
the chat prompt (founder); editing `_observations/` historical memos; any code/prove_ci work.
