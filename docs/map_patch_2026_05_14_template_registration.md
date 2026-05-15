# Documentation Map v1.6 - Template Registration Patch

**Date:** 2026-05-14
**Patch type:** Tier 4 registration addition (two artifacts)
**Predecessor Map:** Documentation Map v1.6 at `ac96447`
**Addendum precedent:** Map v1.6 section 4.2 patch at `46736a0`
**Promotion-certification memo:** this session Commit 1

This addendum is filed per Map v1.6 preamble section 6.2 (registration-as-commissioning)
and follows the Option A patch-addendum path elected in the promotion-certification memo
section 5 Commit 3. The Map's tier structure, preamble, Compression Rule, and Canonical
Declaration are unchanged.

---

## Registration

The following two artifacts, promoted to `docs/templates/` at Commit 2 of this session arc,
are hereby registered at **Tier 4 -- Operational Control & Build Discipline**:

**Per-Surface Constitutional Memo Template v1.0 (+ skeleton companion)**

- **Template memo:** `docs/templates/per_surface_constitutional_memo_template_v1.md`
  Provenance: authored at `5291c46`; promoted at this session (Commit 2, session-start
  HEAD `ce65310`). Twelve-section structure with three classification kinds (required /
  mode-flexible / conditional), per-section authoring guidance, template-evolution provision,
  and promotion gate. Framework artifact per Phase 11 Surface Roadmap section 5.3 at `ba8b58a`.

- **Skeleton companion:** `docs/templates/per_surface_constitutional_memo_skeleton_v1.md`
  Provenance: co-filed at `5291c46`; co-promoted at this session (Commit 2). The
  copy-pasteable artifact spec authors open to begin drafting a per-surface constitutional
  memo. Twelve section stubs with inline guidance comments and standard predecessor/footer
  scaffolding. Companion to the template memo; registered at the same tier.

Both artifacts are registered as a unit. Future Map revisions may separate the two entries
if the skeleton diverges in tier or scope from the template; at v1 they share a tier.

---

## Tier 4 rationale

Tier 4 (Operational Control & Build Discipline) governs how the work is done, not what it
produces. The per-surface constitutional memo template governs the process of authoring
per-surface constitutional memos -- a build-discipline artifact for the Phase 11 surface
specification track. The existing Tier 4 entries (Engineering Handoff Checklist v1.1,
Development Playbook (MVP), Recap Review Heuristic) govern how code and recaps are written
and reviewed. The template governs how per-surface constitutional memos are written. Same
family. Tier 3 (Technical Authority) is too high: the template governs document authorship,
not system behavior or inter-module contracts. Tier 5 (Archival & Reference) understates
the template's active-use status -- every future spec author opens the skeleton at session
start. Tier 4 election is recorded in the promotion-certification memo section 5.

---

## Updated Tier 4 entries (complete list post-patch)

- Engineering Handoff Checklist (v1.1)
- Development Playbook (MVP)
- Recap Review Heuristic (Founder Use Only)
- Per-Surface Constitutional Memo Template v1.0 (+ skeleton companion)
  *(registered by this addendum)*

---

## What this patch does NOT register

- None of the four per-surface constitutional memos (E1 / A1 / A2 / A3). Each is
  provisional in `_observations/` and requires its own section 8.4 promotion gate (one
  full cycle observed + founder election). None has met that gate as of 2026-05-14.
- The Surface Admission Test (Roadmap section 5.1) -- predecessor-state not yet met.
- The Doctrine-to-Product Translation Table (Roadmap section 5.2).
- The shipped-vs-admissible split update (E1/A1/A2/A3 all shipped as of `ce65310`;
  admissible set is now E2-light / E3 / F1). This stale entry warrants a full Map v1.7
  sweep in its own session; it is out of scope for this patch-addendum arc.

---

## Cross-references

- `ac96447` -- Documentation Map v1.6 (the patched document)
- `46736a0` -- Map v1.6 section 4.2 patch (Option A addendum precedent)
- `bb0f325` -- Reset Memo v1.0 (section 6.2 registration-as-commissioning)
- `5291c46` -- Per-surface constitutional-memo template v1.0 + skeleton (origin commit)
- Promotion-certification memo -- this session Commit 1
- git mv -- this session Commit 2
