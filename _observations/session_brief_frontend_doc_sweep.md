# SESSION BRIEF - Frontend doc sweep (companion to engine Unit E1.3)

**Repo:** `~/squadvault` (FRONTEND - NOT the engine repo). Run this session there.
**Tool/model:** Claude Code / Opus 4.8. Doc-only.
**Authored by:** engine E1.3 session (HEAD `c05c49e`) as a close-out deliverable per the
founder's scope split: engine items shipped in `squadvault-ingest-fresh`; frontend doc
edits deferred to this session.
**Source:** Document of Record v2.1 Unit E1.3 / Completion Plan v1.0 Unit 1.3 (frontend bullet).

## START - verify first (charter section 3)

1. This brief was authored from the ENGINE repo; the frontend HEAD `4e44bb3` is quoted
   from the Document of Record. **Re-verify it in `~/squadvault`** (`git log --oneline -10`,
   confirm HEAD). If it differs, git wins - rewrite against the actual frontend HEAD and
   flag the discrepancy.
2. Read the frontend repo's own CLAUDE.md / process docs if present; this engine charter
   does not necessarily govern the frontend repo.

## Scope of work (frontend, doc-only)

- **ROADMAP.md** - rewrite the current-position and open-work sections against the actual
  frontend HEAD. Remove stale/discharged items; reflect true shipped state.
- **SETUP.md** - refresh install / run steps against current reality (verify each command
  actually works before documenting it).
- **README.md** - replace boilerplate with an accurate project description and pointers.

## Acceptance criteria (binary)

- A fresh session reading only the chat project prompt + frontend `ROADMAP.md` lands within
  one commit of the frontend's true state (mirrors the engine E1.3 acceptance for the
  engine side).
- Each documented command in SETUP.md is verified runnable, not assumed.
- Doc-only gates for the frontend repo pass (whatever that repo enforces).

## OUT OF SCOPE

- Any engine-repo edits (done in E1.3: `c05c49e` and the E1.3 commit series).
- The chat project prompt itself (the engine E1.3 session drafts it; founder applies it).
- Code changes; this is a documentation sweep only.

## Notes

- The engine-side Document of Record now lives at
  `docs/SquadVault_Product_Document_of_Record_v2_1.md` in the engine repo (filed in E1.3).
  The frontend repo may want its own pointer if it references the plan of record.
