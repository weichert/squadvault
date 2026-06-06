# OBSERVATIONS 2026-06-06 - Project Status Reconciliation

**Session type:** Status reconciliation against goals. Read-only across both repos
(engine + frontend). Doc-only; SKIPS prove_ci. Triggered by a founder check: "are we
still on track -- we were focusing on frontend, shifted to engine lately."

**Engine HEAD:** e794575. **Frontend HEAD:** 2415426. Both read-only this session.

**Verdict:** On track -- arguably ahead. The recent engine focus is NOT drift; it is the
causal tail of completing the frontend founding arc and wiring its voice output into the
live engine. One watch-item (substrate-pull vs the Artisan frame); the guardrail held.

---

## 1. The goal anchor

- **North star:** a universal substrate for niche-aware AI content. Fantasy football is the
  proving ground and calibration set, NOT the product. The Writer's Room is the product; the
  substrate is the precondition.
- **Strategic posture (binding, Reset Memo section 9.3):** the Artisan frame -- ship
  exquisitely to the founder's league (PFL Buddies) FIRST. The disruption/substrate ambition
  is legitimate but explicitly conditional on that.
- **The plan (Operational Plan v1.1):** Phase A (MVP) -> B (reception/rhythm) -> C (voice +
  onboarding) -> D (diagnostic) -> E (operational maturity) -> F (second artifact class) ->
  G (trend detectors). Closing ethos: "Build the button. Press it. Watch what happens."

## 2. Verified current state (re-baselined; prior backlog memory was stale)

Stated up front because it matters for sequencing: several items that a stale list would call
"next" are already shipped. This section re-baselines from git log across both repos so the
next session does not start from a stale brief -- a recurring false-start hazard, and the
direct reason this reconciliation exists.

- **MVP per IRP (Phase A): COMPLETE** -- declared 2026-05-02. Ingest -> recap -> approve ->
  store -> retrieve -> distribute -> read by a real member.
- **Phase 11 surfaces E1, A1, A2, A3, F1: shipped/live.** A3 (Championship Timeline) is
  implemented and maintained (regenerated for the 2025 close, wired into the A1/A2/A3 Supabase
  archive sync), not spec-stage. Template v1.0 is promoted (git mv to docs/templates/ + cert
  memo + Map registration). The Surface Admission Test framework is authored. F1 rivalry
  chronicle has gone live. (These four are the clearest stale-list corrections.)
- **Fabrication prevention: shipped.** Arc 1-3 (closure 2026-05-17) plus the Cat 13
  DRAFT_AUCTION_DOLLAR category -> 13+ verifier categories. Driven by the real 2026-05-16
  commissioner review where 12 of 13 2025 recaps needed a factual edit. Directly serves the
  Artisan frame: hard factual errors do not reach the commissioner.
- **Frontend: substantially built and active.** Founding Session F1-F3 complete and verified
  live; B2 re-run-from-Office; CI/Node/Vercel guards; PWA polish; "frontend continuity
  surface." 33 frontend commits this month -- not stalled.
- **Voice integration (frontend founding -> engine recaps): just closed.** PFL Buddies now has
  a LIVE engine voice row (OBSERVATIONS_2026_06_05_PFL_VOICE_LIVE.md); recap generation injects
  it (creative_layer_v1, `if voice_profile:`). "Voice-live demonstrated end-to-end" proved the
  mechanism on 2026-06-05.
- **Open / not yet done:** no voice-QUALITY review has ever run (the mechanism works; whether
  the OUTPUT sounds like PFL Buddies is unasked). Phase B/C/E (operational rhythm, member
  onboarding, maturity) are the next on-mission frontier.

## 3. Is the recent engine focus drift? No.

Timeline (verified commit dates): frontend culminated 2026-06-04 into 2026-06-05 00:00
(founding arc, B2 re-run, CI/PWA, continuity surface). Engine ran 2026-06-05 15:00 ->
2026-06-06 00:35. A clean ~36-hour handoff, and the engine chain is causally linked end to
end: finished the founding session -> tried to make its voice reach live recap generation ->
that surfaced a fixture-fingerprint defect -> fixing it unblocked the DRAFT_AUCTION_DOLLAR
verifier -> which surfaced the 2021 DRAFT_PICK gap -> which raised the manual-import question.
Each step caused the next. That is deep work that found adjacent issues, not an aimless pivot.
The voice-bridge work in particular IS frontend/engine integration, not a departure from it.

## 4. Watch-item: the substrate pull

The chain's tail pulled toward forward/abstract territory -- the manual-import constitutional
question is substrate-breadth work, explicitly NOT fantasy-football-MVP work. That
gravitational pull toward the substrate vision is precisely what the Artisan frame (section
9.3) guards against. The guardrail held: that frame PARKED itself as a founder decision and
decoupled from 2021 rather than drifting into building. No harm; it is the thing to stay
alert to. The discipline of parking (not building) forward questions is working as intended.

## 5. Reconciled "next up" list (non-stale, as of e794575)

- **On-mission, doable now (off-season):**
  - Voice-quality calibration pass -- does the now-live PFL voice produce recaps that sound
    like PFL Buddies? (RECOMMENDED next; see section 6. Session brief filed alongside this memo.)
  - Member onboarding (Phase C) -- profiles for the 10 PFL Buddies members; Member Onboarding
    Contract Card.
  - Clubhouse / member-experience frontend polish.
- **Season-gated:** live 2026 weekly recaps + reception rhythm (Phase B) -- gated on NFL
  Week 1 (~2026-09-08).
- **Parked / founder-decision (no clock):** manual-import substrate adapter (frame at 93578fd,
  D1-D6 pending ratification); 2021 DRAFT_PICK supersession memo (cause established, recoverability open).
- **Gated / future:** Phase 11 Closure Memo (6 certifications, plausibly 2026-late/2027);
  real-NFL-storyline historical calibration (architectural follow-on).
- **Candidate / optional:** Arc 4 -- cumulative season-points verifier category (named in the
  Arc 1-3 closure memo; no category currently covers "228.50 total points"-shape claims).

## 6. Recommended next move

**Voice-quality calibration pass.** The voice pipe is live but its output was never reviewed.
The Artisan frame demands the next question be "is what comes out exquisite for PFL Buddies?"
-- the we-construct-not-me-construct test, on the founder's own league. It is doable now on
2025 historical recaps (no 2026 games until September), it bridges the frontend (founding
voice selection) and engine (recap voice) Steve has been oscillating between, and it returns
focus from engine-mechanics/substrate to league experience -- exactly where "ship exquisitely
to the founder's league" and "press the button and watch" both point. The 2021 and
manual-import threads stay parked with no clock.

## 7. State

- Engine HEAD e794575, frontend HEAD 2415426, both read-only this session.
- Artifacts: this memo + session_brief_voice_quality_calibration_pass.md.
- Doc-only commit: _observations/, ASCII subject, SKIP prove_ci, one topic.
