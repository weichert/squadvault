# Weekly Window Immutability — canonical-set consistency audit, addendum

**Date:** 2026-05-03 (same session as the parent observation)
**HEAD at addendum-write:** `d76e71b` on `origin/main`
**Supersedes:** nothing
**Amends:** `_observations/OBSERVATIONS_2026_05_03_WEEKLY_WINDOW_CANONICAL_SET_CONSISTENCY.md`
(commit `d76e71b`) — the §5.1 surgical-edit recommendation assumed the
Temporal Scoping Addendum was tracked at `docs/addenda/` alongside the
other binding addenda. It isn't. This addendum lands the routing
decision (Reroute A: tracking gap is the finding) and adds the new
OPEN_QUESTION the parent memo missed.

**Status:** FINAL

---

## 1. What the parent memo got wrong

The parent memo's §5.1 drafted a surgical-edit replacement for the
Implementation Note at the foot of `Weekly_Recap_Context_Temporal_Scoping_Addendum_v1_0.md`.
The recommendation assumed the addendum file was tracked at a path
parallel to the other binding addenda, which all live at
`docs/addenda/` as `.docx`:

```
docs/addenda/
  Canonicalization_Policy_Addendum_v1_0.docx
  Canonicalization_Semantics_Addendum_v1_0.docx
  EAL_Persistence_Clarification_Addendum_v1_0.docx
  (no Weekly_Recap_Context_Temporal_Scoping_Addendum)
```

A `find` and `grep -ril` pass at HEAD `d76e71b` confirms the addendum
file is not present anywhere in the repo. The only repo-side
references to the addendum are:

- `src/squadvault/core/recaps/context/league_history_v1.py:11, 27, 657`
  — three docstring callouts naming "the Weekly Recap Context Temporal
  Scoping Addendum (v1.0)" as the governing invariant.
- `src/squadvault/core/recaps/verification/recap_verifier_v1.py:129` —
  one docstring callout, identical phrasing.
- `_observations/OBSERVATIONS_2026_05_03_WEEKLY_WINDOW_CANONICAL_SET_CONSISTENCY.md`
  — the parent memo itself.

The brief flagged a `.docx` vs `.md` *format* asymmetry across the
canonical set. It did not flag the *location* asymmetry: three binding
addenda are tracked, one is not. The §5.1 surgical-edit recommendation
is withdrawn because the canonical-location question dominates the
canonical-text question — you cannot responsibly edit a document whose
canonical location is itself unsettled.

## 2. What the parent memo got right

The diagnostic stands. The Hard Invariant is real, the conformance is
real, the W13 validation is real, and the canonical-set is
substantively consistent at the level the parent memo audited. T9 is
still a STALE_CLAIM in the strict sense — the addendum's
Implementation Note describes a pre-`bd680e3` shape that no longer
matches shipped reality. What changes here is only the recommended
action: from "surgical edit candidate" to "no edit pending tracking
decision."

## 3. The tracking gap

Code references the addendum as binding canonical authority (4
docstring callouts). Operating principle from the Constitution and
EAL Persistence Addendum: code that names a binding doc by version
number is asserting a contract relationship to that doc. The doc must
exist, be retrievable, and be reproducible.

Today, retrievability is asymmetric:

- **In project knowledge:** the addendum is uploaded as the canonical
  `.md` source. Reachable from this conversation; reachable for any
  future session that has project knowledge access.
- **In the repo:** the addendum is not present. A future contributor
  cloning the repo and reading `league_history_v1.py:11` finds a
  reference to a document that does not exist alongside the code.

This is not necessarily a defect. Two design intents could account
for it:

- **Project-knowledge as canonical store** — Steve's project knowledge
  is the source of truth for canonical addenda; the repo references
  them by name and trusts that the project-knowledge layer maintains
  retrievability. The other three addenda being in `docs/addenda/` is
  an artifact, not a pattern.
- **Repo-as-canonical-store with this addendum as oversight** — the
  pattern is "binding addenda live at `docs/addenda/`," and the
  Temporal Scoping Addendum is missing because it postdates the
  pattern's establishment.

Both are defensible. The canonical set itself is silent on which
intent is correct. The right next step is a governance decision, not
an edit.

## 4. Revised classification

Parent memo's table:

| Bucket | Count |
|---|---|
| CONSISTENT | 11 |
| STALE_CLAIM | 1 |
| OPEN_QUESTION | 4 |
| REDUNDANT | 1 |

After this addendum:

| Bucket | Count |
|---|---|
| CONSISTENT | 11 |
| STALE_CLAIM | 1 (no recommended action; pending tracking decision) |
| OPEN_QUESTION | 5 (adds Q5) |
| REDUNDANT | 1 |

T9 stays a STALE_CLAIM — the parent memo's diagnosis is unchanged.
The §5.1 surgical-edit recommendation is the only thing being
withdrawn.

## 5. New OPEN_QUESTION

**Q5 — Canonical store for binding addenda.** Three binding addenda
(Canonicalization Policy, Canonicalization Semantics, EAL Persistence
Clarification) live at `docs/addenda/` as `.docx`. The Weekly Recap
Context Temporal Scoping Addendum lives in project knowledge as `.md`
and is not tracked in the repo. Code references the Temporal Scoping
Addendum by version number from 4 docstring callouts. The canonical
set has no documented rule for where binding addenda must live.

Three plausible governance answers:

- **Repo-canonical** — promote Temporal Scoping Addendum into
  `docs/addenda/` (likely as `.md`, since the source is `.md`; or
  convert to `.docx` for parity). Apply T9 surgical edit at the same
  time. Single commit. Establishes the pattern: binding addenda live
  in the repo.
- **Project-knowledge-canonical** — declare project knowledge the
  canonical store for binding addenda; treat the three `.docx` files
  in `docs/addenda/` as denormalized copies of the project-knowledge
  source and document the asymmetry explicitly somewhere in the
  Documentation Map. T9 edit applies to the project-knowledge `.md`
  only.
- **Both** — repo-tracked for retrievability under clone, project-
  knowledge-canonical for authoring and update workflow. Document the
  sync expectation in the Documentation Map. Higher maintenance cost,
  highest retrievability.

This is a governance decision, not an audit finding. Surfaced for
deliberate handling rather than silent drift. *Not urgent.* The
absence has not produced an observable defect; the conformance work
landed correctly even with the addendum un-tracked.

## 6. What this addendum does NOT do

- **Does not apply T9.** Withdrawn pending Q5 resolution.
- **Does not modify the parent memo.** The classification stands at
  the time it was made; this addendum amends the §5.1 recommendation
  only.
- **Does not reopen architectural decisions.** The Hard Invariant
  stands; the conformance stands; the audit's substantive findings
  stand.
- **Does not promote the addendum into the repo.** That would be
  Reroute B; Reroute A was selected.
- **Does not propose a Q5 answer.** The question is named for future
  governance handling.

## 7. Stop signal

Routing decision recorded. Tracking gap surfaced as Q5. T9 surgical
edit withdrawn pending Q5 resolution. Memory directives #9 and #10
landed in this session capture both the closure of the temporal
scoping thread and this surface finding.

Two commits this session: parent memo at `d76e71b`, this addendum
next. Both single-topic. The recap-quality thread can advance to Step
2 (score-string pre-rendering) — Q5 does not gate further code work.

Read first. Classified. Rerouted. Memo and addendum written.
