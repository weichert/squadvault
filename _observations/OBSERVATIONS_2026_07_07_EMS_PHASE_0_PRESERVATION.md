# OBSERVATIONS 2026-07-07 — Environmental Memory (EMS) Phase 0 Preservation

**Status:** Founder-ratified (DECIDE session, 2026-07-07)
**Lane:** DECIDE — adjudication and preservation only. No engineering work authorized by this memo.
**Companion artifacts:** `Environmental_Memory_Founder_Draft_v0_9.md` (vision, non-binding);
`SquadVault_EXECUTE_Brief_EMS_Phase_0_Landing_2026_07_07.md` (landing brief).

---

## 1. Purpose

Preserve the Environmental Memory ("EMS" / "The Living Clubhouse") founder vision, record its
constitutional evaluation, ratify the pre-launch architectural hooks, and register EMS as a
post-Closure-Memo candidate. This memo authorizes nothing beyond preservation. The Fantasy
Football MVP calendar (Test B, pre-season room UI completion, Unit A7 baseline) is unaffected
and continues to outrank all EMS work.

## 2. Vision summary (one sentence)

Every coach has one lifetime office; every league becomes another chapter in that office's
story. (Founder's formulation, executive vision of the v0.9 draft — attribution note: this
sentence originates in the founder draft, not in the director review.)

## 3. Constitutional evaluation — alignment

- Derived-never-authoritative holds: EMS renders environments from approved data and never
  writes canonical league memory.
- Human curation over algorithmic decoration matches humans-approve-publication.
- Curated placement slots (not freeform design) match the set-piece/hybrid/admin room-map
  discipline.
- League memory remains group-scoped and append-only; EMS does not touch the ledger.
- The Trophy Room Living Hall pivot (baked ambient layer + data-backed, provenance-carrying
  artifacts at defined positions) is EMS architecture in embryo. Fixed/Curated/Persistent maps
  onto master render / plates / seeded artifact rows. EMS names a direction already partially
  shipped rather than introducing a disconnected one.
- Second Module Qualification Checklist core criteria: passes longitudinal memory, narrative
  richness, non-real-time tolerance, memory-over-optimization, governed tone. Fails
  group-centric as drafted (see 4.1).

## 4. Conflicts identified (to be resolved at Phase 1, not here)

### 4.1 Group-centric criterion
EMS as drafted is coach-scoped; Core Qualification Criterion 1 requires group-centric modules.
Resolution paths recorded: (a) founder-ratified checklist/constitutional amendment recognizing
coach-scoped longitudinal memory as a second admissible scope; (b) reframe EMS v1 as
league-scoped with portability deferred. Director recommendation: path (a), authored as an
explicit amendment, never as a quiet exception. Founder direction ratified 2026-07-07:
amendment direction is minimal-scope — Group Memory, Coach Memory, Hybrid Artifact References
only. Speculative scopes (Family, Organization) are excluded from constitutional text until a
named consumer exists. Amendment drafting is Phase 1 work.

### 4.2 Consent model of the Environmental Profile
The draft's "quietly establish an Environmental Profile" conflicts with the Data Ethics and
Trust posture and the voice-profile precedent. Ratified correction: the onboarding conversation
may be casual, but it produces a visible Environmental Profile that the coach reviews, edits,
and approves before any office renders from it. The magic lives in the reveal, never in hidden
profiling. Recognition-not-explanation is the emotional goal of the reveal; it is not the
consent model of the data.

### 4.3 Retention-adjacent business framing
"Encourages long-term subscriptions by increasing emotional value" is admissible under
monetization-alignment only with a bright line. Ratified invariant (canonical wording):

> The office evolves because history happened — a season archived, an artifact earned, an
> event attested — never because a user logged in, clicked, or spent time.

Wall-clock time, visits, and streaks are inadmissible evolution inputs, permanently.

### 4.4 Trademark symbol
"Environmental Memory (TM)" appears in the draft. Do not use the mark symbol in canonical
documents unless a mark is actually pursued.

## 5. Ratified framing adopted into canon-track language

- **Expression, not personalization.** Personalization says: the system learns me. Expression
  says: the system gives form to memories I have explicitly entrusted to it. EMS is
  environmental expression. This framing feeds the Data Ethics and Trust Positioning Memo at
  its next revision and all EMS specification work.

## 6. Deferred adjudication (recorded, not resolved)

**Capability vs. module.** Two interpretations recorded fairly:

- *Module interpretation:* EMS carries its own data model, UI surface, asset pipeline, and
  approval flow; it is a module and passes through the Second Module Qualification Checklist.
  The voice-profile precedent does not apply (that was a new input to an existing engine
  component under the existing governance model).
- *Platform-capability interpretation:* EMS rendering machinery (profiles, slots, prop
  libraries, snapshots) is module-agnostic infrastructure consumable by future modules; EMS
  content is per-module. Under this interpretation EMS is a platform layer — which is a
  frozen-layer-structure amendment and therefore a *stricter* gate than the checklist, not an
  escape from it.

Ruling: deferred to the Phase 1 qualification session, where it becomes a named centerpiece
alongside 4.1. Rationale: with one module and one league in existence there is no second
consumer to validate the abstraction against; infrastructure abstracted from a single consumer
is speculation. Nothing in Phases 0–2 differs under either interpretation.

## 7. Pre-launch architectural hooks (binding immediately)

- **H1 — Identity keying.** Any personal or coach-scoped data created from this date forward
  keys to the Supabase auth `user_id`, never to `franchise_id`, and never embeds `canonical_id`
  in stored identifiers. Franchise is a league-chapter fact; the coach is the lifetime entity.
- **H2 — No durable league-scoped office deep-links.** `/league/[id]/office`-shaped routes are
  fine as live UI, but must not be hardcoded into stored data, emails, or artifact records. A
  future coach-scoped namespace must be able to arrive without a data migration.
- **H3 — Ambient/data-backed separation stays crisp.** Remaining pre-season room work
  (Clubhouse, Coach Office, Trophy Room drill-down) preserves the baked-ambient vs.
  seeded-artifact boundary everywhere. Every blur is future EMS debt.
- **H4 — No mutable preference blobs.** No mutable `user_preferences`-style JSON columns.
  Future `EnvironmentalProfile` and `PersonalArtifact` structures follow the append-only
  pattern with approval provenance, same as all existing artifact classes.

Hooks are discipline, not construction. No schema, route, or pipeline work is authorized.

## 8. Roadmap placement

- **Phase 0 (this memo):** Preserve. Register EMS as a post-Closure-Memo candidate alongside
  member-generated AI artifacts.
- **Phase 1 (post-Closure-Memo):** Formal Second Module Qualification Checklist run with two
  named centerpieces: the group-centric adjudication (4.1) and the capability-vs-module
  adjudication (6). Minimal-scope amendment drafted here if path (a) is confirmed. Outcome per
  checklist section 6: approve, defer, or reject.
- **Phase 2 (if approved):** Standard four-memo chain (selection-prep, decision-readiness,
  specification, registration). Recorded Increment 1 scope shape: curated placement slots in
  the existing Coach Office for the existing league — swap props, curate one shelf, from a
  founder-approved PropLibrary — with the explicit Environmental Profile approval gate. No
  onboarding conversation, no cinematic reveal, no multi-league, no aging.
- **Phase 3+:** Incremental delivery under standard discipline (founder-ratified tests before
  implementation, numbered migrations, seed pattern per trophy seeds, v5 prompt-pack render
  pipeline, Trophy Room drill-down interaction reuse). Multi-league portability explicitly
  deferred until a second SquadVault league exists; H1 preserves the seam.

The founder draft's "Next Expansion" section proposed subsequent draft editions expanding into
engineering specifications. Ruled out: all specification flows through the four-memo chain.
The vision document stays vision; no parallel spec lineage exists outside `_observations/`.

## 9. Non-actions

Nothing in this memo touches July. Test B (cross-device invite), pre-season room UI
completion before the ~July 18 runbook trigger, and Unit A7's uncontaminated baseline all
outrank EMS work. Phase 0 is complete upon landing of this memo and its companion vision
artifact on main.
