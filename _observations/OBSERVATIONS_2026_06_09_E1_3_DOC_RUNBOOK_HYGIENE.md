# Observations - Unit E1.3: Doc/runbook hygiene sweep (engine side)

**Date:** 2026-06-09
**Content commit:** `58b498a` · **Ledger commit:** this commit
**HEAD at authoring:** `58b498a`
**Source brief:** `_observations/session_brief_e1_3_doc_runbook_hygiene_sweep.md`
**Scope split (founder):** engine items here; frontend items in
`_observations/session_brief_frontend_doc_sweep.md` (separate `~/squadvault` session).

---

## What shipped (engine side)

- **Document of Record filed in-repo** at `docs/SquadVault_Product_Document_of_Record_v2_1.md`
  (was chat-only). Registered via `docs/map_patch_2026_06_09_document_of_record.md`; both
  new top-level docs added to `_GRANDFATHERED_TOP_LEVEL_DOCS` in the suite test.
- **Charter amendment v1.0.1** (CLAUDE.md): the Product-plan-of-record pointer now resolves
  to the in-repo path; logged in section 9, founder-approved. First exercise of the
  section-9 amendment process.
- **Frontend session brief authored** for the deferred `~/squadvault` ROADMAP/SETUP/README sweep.

## Verification findings (git won over the Document of Record's own task list)

1. **Runbook DB-path fix was already done.** Unit E1.3 lists "fix
   `data/squadvault.db` -> `.local_squadvault.sqlite`" as work, but
   `docs/runbooks/distribution_v1.md` already used the canonical path; the fix landed at
   `215cb39` ("docs: fix runbook DB path drift"). The Document of Record and Completion
   Plan pre-date / did not track it. Recorded discharged in STATE.md; no edit made. The
   surviving `data/squadvault.db` strings live only in immutable `_observations/` memos.

2. **The Document of Record was not where the founder thought.** The adjudication said
   "copied to docs/," but the file was absent on first verification (and absent from the
   sibling clone, the frontend repo, Downloads, Desktop). Flagged; the founder then placed
   it at the final path. Lesson reinforced: verify file placement on disk, not from the
   intent to place it.

## The deeper point: this unit closes the retrieval gap

The Document of Record living only in chat is what blocked scoping E1.2 and E1.3 from
Claude Code (the E1.x cluster could not be read in-repo). Filing it - and pointing the
charter at the in-repo copy - means future units scope from `git` + STATE.md + the in-repo
plan, with no chat round-trip. STATE.md's "descriptions live in chat" note was updated to
point at the in-repo path.

## Doc-only path

Per the unit definition, this is doc-only: the four pre-commit gates + the new E1.2 ruff
gate ran on each commit; prove_ci is correctly SKIPPED (no code/proof-surface change).

## Carried forward / founder actions

- **Founder terminal action:** delete the stale sibling clone `~/projects/squadvault-ingest/`.
- **Founder action:** apply the drafted chat project prompt (delivered in the session
  close-out) in claude.ai.
- **Separate session:** the frontend doc sweep per `session_brief_frontend_doc_sweep.md`.
