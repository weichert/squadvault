# SquadVault — Product Completion Document of Record — v2.1

**Date:** 2026-06-09
**Supersedes:** Completion Plan v1.0 and v1.1 (same date; retained unmodified per append-only discipline). v2.0 is self-contained — the consolidated document of record for product completion.
**Authored by:** Claude Fable 5 (planning sessions; all repo claims verified read-only against the repos of record)
**For execution by:** Claude Opus 4.8 sessions against unit briefs herein; Claude Fable sessions where marked
**Engine HEAD verified:** `a9bc451` (2026-06-09 12:07 PT) · **Frontend HEAD verified:** `4e44bb3`
**Status:** Provisional / observational. No tier until founder elects registration. Founder adjudicates every numbered decision (Part 6) before the corresponding session executes. Where this document conflicts with any Tier 0–4 canonical document, the canonical document governs.

**v2.1 (2026-06-09):** Added Unit W.8 (the Memorabilia Pipeline — testimony-derived set dressing for the clubhouse scene), decisions D-Q/D-R, and master-sequence integration. v2.0 content otherwise unchanged.

**v2.1.1 supersession note (2026-06-10):** Part 3 Unit W.6 says the consent model "extends `founding_sessions.consent`." That claim is **superseded** by the ratified W.6 Consent Governance Memo, Section 0 (`docs/SquadVault_W6_Consent_Governance_Memo_v1_2.md`), which verified at frontend `4e44bb3` that the field is mutable, league-level, and a three-boolean bundle — so per-member/append-only/revocable-forward consent is established as a **new** `member_consent_events` system of record, and `founding_sessions.consent` is reinterpreted as the league-defaults layer (D-X). The W.6 unit is otherwise discharged by that memo (decisions D-S through D-X ratified 2026-06-10). DoR body text below is retained unmodified per append-only discipline; the memo governs where they differ on the substrate.

**v2.1.2 supersession note (2026-06-21):** Part 3 Unit W.5 names the trophy custody surface "the
Mantel," and its Display-layer bullet calls the display "the Mantel in the clubhouse scene."
Founder ruling 2026-06-21 (governing memo
`_observations/OBSERVATIONS_2026_06_21_TROPHY_ROOM_NAMING_RULING.md`) **supersedes** that naming.
The trophy-display surface behind the clubhouse trophy-case portal is **"the Trophy Room"** -
already the W.2 nav name at line 113 ("trophy case -> Trophy Room"). The name **"the Mantel"** is
reassigned to the literal mantelpiece fixture holding framed photos, which is the navigation portal
into Mr. Herlth's A/V Room (Unit W.1, "framed photos -> A/V Room door" at line 113). Unit W.5's
identity, fact layer (`trophy_custody_events`), boundary, and four-memo chain are unchanged; only
the display-surface name changes from "the Mantel" to "the Trophy Room." DoR body text below (lines
~119, ~121, ~230, ~238) is retained unmodified per append-only discipline; where it says "the
Mantel"/"the mantel" in reference to the trophy display, read "the Trophy Room" per this note.

---

# PART 0 — WHAT "COMPLETE" MEANS

The completion gate is the project's own, not an invented finish line:

1. **MVP per IRP §3** — ✅ COMPLETE (2026-05-02).
2. **Operational maturity** — Op Plan v1.1 Phases B–E; the six-consecutive-cycle certification is **calendar-gated on the live 2026 NFL season**.
3. **Phase 11 closure** — Closure Memo against the six Reset Memo §8.4 certifications, gated on ≥1 full live cycle. Earliest anchor: **NFL Week 1, ~2026-09-08**.

The binding constraint is the calendar. Engineering's job between now and Week 1 is to enter the season with zero known drift, a measured fabrication baseline, formatted output, and the first warmth surfaces live. The season's job is rhythm, reception, and lore accumulation. Closure's job is honest certification. Everything in this document serves one of those three.

**The product thesis (governs all prioritization):** SquadVault is a provenance-governed memory engine for small communities with long histories, proven first on the hardest test case — a 16-year fantasy league whose members will call out a wrong score. Its defensible position is three stacked moats:

- **TRUST** — the verifier. 19 categories, two pre-registered falsifications, hard failures gate publication. Cannot be replicated by competitors with a press release; it took a year of discipline.
- **VOICE** — governed human testimony. The data nobody else can ever have is not box scores; it is sixteen years of what the members said, captured with consent, attributed, append-only.
- **PERMANENCE** — the league's memory outlives platforms (the 8-MFL-ID history chain already proves the problem), outlives the commissioner's tenure, and — stated plainly because it is the real promise — outlives members. Portability and succession are features.

Trust + Voice + Permanence is also the exact specification for every other community the substrate will ever serve (campaigns, golf trips, rec leagues, book clubs, families). That is the bridge from fantasy football to the platform vision, and it is why the Artisan frame is correct: prove all three moats on PFL Buddies first.

---

# PART 1 — VERIFIED CURRENT STATE & FINDINGS REGISTER

## 1.1 Engine (`weichert/squadvault`, HEAD `a9bc451`, 1,248 commits)

- Tests: **2,346 passed / 4 skipped / 40 subtests** in 99s. Mypy clean on `core/` (69 files). Ruff: 10 errors (R1).
- Surfaces shipped: **E1, A1, A2, A3, E2-light (`993e97f`), F1 (live)**. Archives populated on disk.
- Voice bridge shipped (`7ee2c2d`); unexercised live.
- Fabrication research **converged**: ceiling on context-block manipulation established by two pre-registered falsifications; matchup anchors disabled (`47df707`, ratified `353bb64`); FAAB suppression falsified (`3a9cfd3`); D50 unwired; D39 over-count removed; SERIES tie-aware (`697ffd5`); chronicle docket grammar fixed at source (`2bb33d0`).
- Failure-rate attribution: 0.94 is the **stale-corpus** rate (124/163 rows pre-date the score pre-render fix; post-fix SCORE_VERBATIM 3/39 vs 124/124 pre-fix). **Current-pipeline rate unmeasured** — Part 3 fresh generations are the one open instrument.
- Model pinned `claude-sonnet-4-20250514`; DRIFT ruled out.

## 1.2 Frontend (`weichert/squadvault-frontend`, HEAD `4e44bb3`, 53 commits)

- Member Office + franchise directory shipped (`f0a40ed`, `4e44bb3`). Migrations 008 + 009 committed. **D6 structurally resolved** (era-correct names via `franchise_season_names`; owner-silence per silence-over-speculation).
- All major routes live: landing, auth, Clubhouse, Office + ceremony, full founding session, archive (recaps/records/rivalries), Trophy Room (display entries only — see R6), members.
- Governance tests G1/G3/G4/G6/G7/G9 in place; RLS, no-DELETE policies across tables.

## 1.3 Discharged — DO NOT RE-OPEN

Cavallini/Mahomes rename (`a5d27dd`) · seasons-count corrections (supersession memos `c4b4436` + A2 amendment; fold-in at natural touch-points by design) · A3 archive generated · migrations 008/009 committed · Member Office shipped / D6 resolved · template v1.0 promoted · E2-light shipped · matchup-anchor and FAAB context-manipulation levers (falsified; closed).

## 1.4 Findings register

- **R1 — Ruff drift, F1 chronicle path.** 10 errors in `src/squadvault/chronicle/generate_rivalry_chronicle_v1.py`, `src/squadvault/consumers/rivalry_chronicle_generate_v1.py`, `src/squadvault/consumers/editorial_review_week.py` (E401, E402×3, F401, I001×4, UP037; 7 auto-fixable). Version-stable rules → genuine drift. Confirms pre-commit gates lack ruff.
- **R2 — Ruff unpinned** in `requirements.txt`/`pyproject.toml`. Latent CI-vs-local divergence.
- **R3 — Chat project prompt severely stale** (claims Phase 10 / `b9f495c` / 1,192 tests). Highest-leverage token fix; generates re-baselining tax every session.
- **R4 — Frontend continuity docs stale** vs own HEAD (`ROADMAP.md` lists voice bridge unbuilt and Member Office as stub; `SETUP.md` stale since M2; `README.md` boilerplate).
- **R5 — Published narratives carry no presentation formatting; no formatting review exists in the publication path.** Verified against `archive/recaps/2025/week_07__v27.md`: setext title, undifferentiated prose, raw bullet facts block; distributed over `group_text_paste_assist` where markup renders literally. Verifier gates facts only; Office review surfaces no presentation checklist. Derived-layer gap; facts untouched by the fix.
- **R6 — Trophy custody ("stolen trophy") system exists as founder vision only.** `trophy_room_entries` is a flat display table; zero references to custody/transfer/possession in either repo. Custody-over-time requires a new append-only event class. Registered as Unit W.5.

---

# PART 2 — TRACK E: ENGINEERING & OPERATIONS (the completion spine)

## Window 1 — Off-season hardening (now → late Aug 2026)

**Unit E1.1 — Lint fix + ruff pin** (Opus, short). Fix the 10 R1 errors (verify the 3 manual E402s aren't legitimate late-imports needing per-file-ignores like their siblings); pin ruff. Gates per discipline: ruff/mypy/pytest, prove_ci on clean tree, separate paste turns. **Acceptance:** `ruff check src/squadvault/` zero; pin present; suite green.

**Unit E1.2 — Pre-commit gate hardening** (Opus). Add ruff to pre-commit (D-A: pytest subset recommended NO — prove_ci owns the 99s suite; ruff's absence is what caused R1). Enumerate ALL registry marker-blocks per the F2/F5 post-mortem. **Acceptance:** a planted lint error blocks at commit; gate registered.

**Unit E1.3 — Doc/runbook hygiene sweep** (Opus, doc-only; banner/xtrace/allowlist/docs-Map gates; skips prove_ci). Runbook DB-path fix (`data/squadvault.db` → `.local_squadvault.sqlite`); frontend ROADMAP/SETUP/README rewrite against HEAD; **chat project prompt rewrite** (session drafts, founder applies — anchor, don't narrate); delete stale sibling clone `~/projects/squadvault-ingest/` (founder terminal). **Acceptance:** a fresh session reading prompt + ROADMAP lands within one commit of true state.

**Unit E1.4 — Part 3 fresh-generation fabrication baseline** (Fable protocol session + Opus execution session). Pre-register before generating: n (D-B: 24–36 across discriminating weeks spanning the pre/post-2021 substrate split), category thresholds, diagnose-only boundary. Output: the live-pipeline rate by category; non-score residual (FAAB/series/streak/superlative) is the headline. Doubles as Closure cert-6 evidence. **Acceptance:** pre-registered protocol memo + results memo in `_observations/`; no pipeline changes in-session.

**Unit E1.5 — Narrative presentation spec + formatting gate** (closes R5; two sessions).
- **E1.5a — Presentation spec** (Fable): canonical artifact structure at the render layer — title block, per-matchup sections, transactions block, standings note — with per-channel renderings: web prose (typographic; consumes W.2's design language per D-M), plain-text group chat (no literal markup; the verified W7 channel reality), and **print-ready** (this channel is the Almanac's on-ramp, Unit L.8). Facts block byte-identical across renderings. Short spec in `docs/`.
- **E1.5b — Formatting gate** (Opus): four-step playbook — pre-render structure in `render/`, refactor consumers, deterministic structural lint (title present; facts block intact and unmodified; paragraph bounds; no orphaned markup for target channel) running alongside the verifier pre-approval; presentation checklist in the Office review UI. SOFT by nature — formatting flags, never blocks on style alone; facts-block-modified is the one HARD condition. D-F: standalone lint, not a verifier category (keep the verifier's contract purely factual).
- **Sequencing: E1.5a lands before NFL Week 1** so the season's first live recap publishes formatted.

**Unit E1.6 — `promote-version` lifecycle** (optional; D-C recommend defer to season evidence).

**Unit E1.7 — Surface Admission Test first exercise** (condition-gated; satisfied naturally by W.1 and W.5's four-memo chains — do not manufacture a candidate).

## Window 2 — Live season (Sept 2026 → Jan 2027)

**Unit E2.1 — E1 revision-point at Week 1** (Fable, ~2026-09-08). Cycle-count toward closure; backfill-vs-live disposition; channel judgment per E1 spec §6.6.

**Unit E2.2 — Weekly cycle execution** (Opus recurring; Fable shadow on cycles 1–2 only, then drop if clean). Ingest → generate → verify → **formatting checklist** → commissioner review → approve → distribute → record reception. Voice bridge gets first live exercises; log per the calibration-pass format. Six consecutive on-schedule cycles = Op Plan Phase B exit. Target ≤1–3 hrs/week commissioner time.

**Unit E2.3 — Member onboarding (Tracks C+E)** (Opus drafting; founder relationship work). Ten member profiles; Onboarding Contract Card → Tier 2. The Member Office, A/V Room (W.1), and Historian Interviews (L.1) are now the destinations that make onboarding land — sequence outreach to coincide with W.1 going live.

**Unit E2.4 — Mid-season voice retrospective** (Fable, ~Week 8). Consumes reception + voice-bridge observations.

## Window 3 — Phase 11 closure (post-season, earliest ~Feb 2027)

**Unit E3.1 — Evidence assembly** (Opus). Mechanical compilation per Roadmap §6.2: commit hashes + memo paths per surface (cert 1); per-surface §6 invariants re-read against operational artifacts (cert 2); reception + founder judgment (cert 3); shipping-pattern audit incl. honest W7-saga accounting (cert 4); framing audit — **W.7's drift-flag memo is a primary exhibit** (cert 5); editorial_actions ledger + E1.4 baseline + in-season verifier record (cert 6).

**Unit E3.2 — Phase 11 Closure Memo** (Fable). The completion event. Phase 12+ becomes authorized, or doesn't, per the memo. This document does not pre-determine the outcome; it does register the Phase 12 candidate slate (Part 4) so the Closure Memo session inherits a real option set.

---

# PART 3 — TRACK W: THE WARMTH TRACK (clubhouse, media, trophies, docket)

Parallel to Track E; not calendar-gated except as noted. All new surfaces enter via the four-memo chain; new fact classes via the Manual Fact Import constitutional frame; anything touching likeness/voice/words via W.6 consent governance. **Standing law for this track and Track L: member words can become facts (attributed, consented, append-only); member behavior is never measured. No telemetry, no autonomous publication, no engagement loops.**

**Unit W.1 — Mr. Herlth's A/V Room** (FIRST BUILD of the track). Archival photo/video room for the existing media corpus. Supabase Storage; append-only media entries; **human-ratified** provenance tags (contributor/date/season/event — never AI-guessed); room-level consent ratification; member captions = first arrival of the governed-testimony fact class; marginalia on items = asynchronous communal reveling (no synchronous watch-party in v1). Four-memo chain (genuine SAT exercise #1). Opus builds against spec; founder ingests media via an Opus-built upload/tagging surface. D-G: photo+video read paths, photo-first tooling.

**Unit W.2 — Art-direction pass ("den, not SaaS")** (Fable authors **Design Brief v2 Addendum**; Opus applies, one surface-cluster per session). Named aesthetic (wood/brass/felt; polaroids, ticket stubs; VHS warmth; 80s ephemera), typography, texture; the **2.5D illustrated clubhouse scene as navigation hub** — trophy case → Trophy Room, framed photos → A/V Room door, corkboard → bulletin board, **answering machine → W/L.4**, toggleable ambient 80s radio. Adjudicated NOT full 3D (cost/mobile/accessibility/maintenance — do not re-open without new evidence). Season archives presented as a shelf of labeled VHS tapes in the A/V Room (aesthetic detail, zero schema impact). D-H: founder ratifies the aesthetic before application sessions.

**Unit W.3 — The Corkboard** (Opus, one session). Finite, dated, chronological, commissioner-published bulletin board on the Clubhouse home. **Not a feed:** no infinite scroll, no algorithmic ordering, no unread counters, no badges. Push stays per D4.1-Gamma (archive-resident + push at notable moments).

**Unit W.4 — Writer's Room pitch docket** (the engine of recurring delight). Autonomous **generation**, human **publication**: Signal Scout proactively drafts artifacts at detected momentous occasions; drafts queue in the Office as pitches — approve / edit / kill. Silence-over-speculation applies to momentousness: zero pitches in a quiet week is the system working; volume is never a target. Artifact classes admitted individually via SAT; **W.6 is a hard predecessor for any class using member likeness or voice.** Four-memo chain; the largest spec of the track. D-I: first class = throwback pieces (pure substrate-derivable, zero consent surface, exercises docket mechanics safely). Subsequent classes feed from Track L: obituaries (L.6), Tale of the Tape (L.7), Gazette pages (L.8), press-conference transcripts (post-W.6), trophy-heist features (post-W.5).

**Unit W.5 — Trophy custody system ("the Mantel")** (closes R6).
- **Fact layer:** new append-only `trophy_custody_events` class — (trophy_id, from_franchise, to_franchise, occasion, season/week, ratified_by, ratified_at). Commissioner-ratified manual facts per the Manual Fact Import frame; current holder is a **derived read, never stored mutable state**. Frontend migration matches every sibling (append-only, RLS, no DELETE); engine-side canonical home per the frame's adjudication. Historical backfill = founder ratification work, same dignity as oral history.
- **Display layer:** the Mantel in the clubhouse scene — each traveling trophy with its **provenance chain** ("held by Miller's Genuine Draft since 2025 W9 — taken from Stu's Crew — 7th transfer in trophy history"), full custody timeline on tap, era-correct names via `franchise_season_names`.
- **Narrative layer:** custody events are Signal Scout-visible — trophy heists are exactly the momentous-occasion class W.4 pitches on.
- **Boundary:** heists are documented history rendered with relish — no points, no theft leaderboards, no custody-streak mechanics.
- Four-memo chain (genuine SAT exercise #2). D-J: founder ratifies the trophy taxonomy (names, origin stories, transfer rules **as the league actually plays them**) before the spec. D-K: backfill depth — honest gaps beat speculated completeness.

**Unit W.6 — Consent governance memo** (Fable; constitutional). The consent model for member likeness, recorded/synthesized voice, attributed quotes, media appearances: captured once, ratified per-member, append-only, **revocable-forward** (revocation stops future use; never rewrites the past record). Extends `founding_sessions.consent`. Hard predecessor to: W.1 attribution-level captions, W.4 press-conference class, L.1, L.3 reveal mechanics, L.4, any audio rendering.

**Unit W.7 — Framing drift-flag memo** (Opus, doc-only, one sitting — DO FIRST on this track). Records that the 2026-06-09 vision sessions surfaced three engagement-shaped framings ("drive constant app/revisits," "constantly updated feed," "engagement evaluated to surface storylines") and each was caught and reframed **before any build** (worthy-of-visits / corkboard / words-become-facts-behavior-never-measured). Cert-5 asks whether framing drift occurred and what was done; "founder caught it in brainstorming" is the strongest possible ledger entry. `_observations/`, no tier.

**Unit W.8 — The Memorabilia Pipeline (testimony-derived set dressing).** The integration tissue between L.1 (interviews), W.1 (media corpus), and W.2 (the scene): lore items detected in member testimony become **proposed** environmental artifacts — a tradition mentioned in an interview surfaces matching candidate photos from the A/V corpus to hang by the draft board; a remembered favorite becomes proposed wall ephemera. The Writer's Room pattern applied to space: **autonomous detection and proposal, human approval, then placement.**
- **Provenance on the walls:** every placed item carries a tappable receipt — the attributed interview quote (or ratified tradition record) that earned it its spot ("hung here because Robb told the historian about it, March 2026"). The clubhouse is not decorated; it is **cited**. The room becomes a rendered index of the league's testimony and grows more personal with every interview and season, the way a real den accumulates.
- **Match ratification:** AI proposes photo/lore matches; humans ratify — identical law to W.1's tagging (never AI-asserted). Detection over testimony is a Signal Scout-class read; placement pitches ride the W.4 docket once it exists (set-dressing pitch class), or a lightweight approval queue before it.
- **Placement authority splits by space (D-Q):** communal walls = commissioner-approved; each member's own coach's office = **member-approved** — members curate their own office from their own testimony, the most personal feature in the product and pure expression, never measurement.
- **Real artifacts over synthesized decor (D-R):** standing preference for actual corpus media (the real photo of the guys at the real concert) over manufactured items. Where no corpus item exists, era-evoking **original** ephemera in the W.2 design language — never reproductions of copyrighted posters, album art, or branded material; no member likeness in generated art ahead of W.6.
- **Ceremonial accumulation, not churn:** items are added occasionally and announced on the corkboard ("new on the wall"); the scene never reshuffles itself. A constantly-changing room would be a novelty loop wearing nostalgia's clothes.
- Predecessors: W.2 (the scene), W.1 (corpus + ratified tagging), W.6 (testimony consent), L.1 (the testimony source — the pre-draft interview wave is the pipeline's first fuel). Route: rides the L.1 and W.4 chains rather than its own; register as a §-section in each spec.

---

# PART 4 — TRACK L: THE LORE TRACK (voice, ritual, legacy — the joy engine)

This track answers "what are we missing." It is where the product becomes beloved rather than merely trusted, and where the Voice and Permanence moats get built. Same standing law as Track W. Units ordered by recommended sequence; calendar anchors noted.

**Unit L.1 — The Historian Interviews (multi-perspective oral history)** ⭐ *one of the two biggest unbuilt ideas.*
Extend the founding-session pattern from the commissioner to **all ten members**: the engine conducts a consented, structured interview with each member — the 2016 championship, the 0-14 season, the trade everyone still argues about, how they joined. Every account preserved **attributed and unmerged** — no synthesized consensus, ever. Display: per-event "as remembered by" panels in the relevant archive surfaces and Member Offices, alongside the verified factual record. The gap between what the ledger proves and what each member swears is the league's richest comedy and its deepest lore.
- Architecture: reuses founding-session machinery (`exchanges` jsonb, consent, topic coverage) — a `member_history_sessions` sibling, not new invention.
- Constitutional shape: testimony is a fact-about-what-was-said; it never contaminates the event ledger. Verified facts and remembered accounts render as visibly distinct layers.
- Predecessors: W.6. Natural pairing: run interviews during E2.3 onboarding — the interview IS the onboarding hook ("the league historian would like a word").
- Route: four-memo chain + Manual Fact Import frame (testimony class formalization). Fable spec; Opus build.
- **Calendar note:** interviews conducted during the season capture the league mid-flight; a pre-draft sweep in August is the ideal first wave (D-N).

**Unit L.2 — Ask the Historian (verifier-gated conversational memory)** ⭐ *the flagship; the marketplace-defining capability. Registered as the lead Phase 12 candidate — NOT summer work.*
Conversational, read-only Q&A over the substrate: "What's our record in games decided by under 3?" "When did Eddie last beat KP in the playoffs?" — answered in league voice, with **every factual claim passing the same verifier path that gates recaps**, and tap-through receipts to the anchoring facts (the claim-level-provenance idea, here as the answer format rather than a separate feature). Everyone else's "chat with your data" hallucinates; this one structurally cannot, which converts the project's deepest engineering asset into the feature a member touches weekly.
- Why Phase 12: ad-hoc generation needs the full verification path at interactive latency, a refusal posture for unanswerable questions (silence-over-speculation as UX), and an admission decision for an interactive surface class. None of that is a summer unit; all of it deserves the chain.
- Pre-work that IS admissible now: E1.4's baseline (measures the generation path Ask-the-Historian would ride) and the E1.5 presentation spec (defines the receipt rendering).
- **Boundary:** read-only; no advice, no projections, no "who should I start" — historical memory only. The refusal message is a product feature: "The ledger doesn't say."

**Unit L.3 — The Vault (sealed letters / time capsules).**
At draft day, each member writes a sealed message — trash talk, bold claims, a note to their December self. Sealed (commissioner cannot read; enforce at RLS layer), timestamped, **revealed at a scheduled ceremony** (season's end, or championship week). The reveal artifact juxtaposes each letter with what the ledger actually recorded — the system never predicts anything; it preserved human words and kept honest books, and the comedy emerges from the collision. Letters become testimony-class facts at reveal (consent captured at writing).
- Small build, enormous joy-per-hour. Frontend: compose+seal UI, scheduled-reveal job, reveal ceremony page. Engine: reveal artifact class via W.4 docket.
- **Calendar anchor: must ship before the 2026 draft (August) to capture this season's letters.** This is the track's hardest deadline. D-O.
- Predecessors: W.6 (consent at writing). Route: four-memo chain (light — likely the fastest chain yet run).

**Unit L.4 — The Answering Machine (audio testimony).**
An 80s answering machine in the clubhouse scene: members leave voice messages — trash talk, reactions, toasts. Messages are consented, attributed, append-only testimony; playable in the A/V Room; transcribable into the quote record. The most natural voice-capture device imaginable, and it makes the 80s aesthetic functional rather than decorative.
- Predecessors: W.2 (the scene), W.6 (voice consent), W.1 (storage + playback patterns).
- Boundary: no AI voice synthesis here — this is **recording** members, the safest possible audio feature. Synthesis (league radio readings of approved artifacts) remains a separately-gated post-W.6 rendering class.

**Unit L.5 — Awards Night (the annual institution).**
End-of-season awards ceremony artifact: superlatives computed from the verified record (highest single-week score, bench-points hall of shame, closest-game survivor), award names drawn from league lore (founder ratifies the slate — D-P), commissioner-hosted reveal, winners enshrined permanently in the Trophy Room with provenance. Annual ritual = the season's capstone and the archive's yearly heartbeat. Pairs with L.3's reveal into a single **Season Finale ceremony** if the founder elects.
- Substrate-derivable + ratified award names; minimal consent surface. Route: four-memo chain; first eligible for the 2026 season's end (~Jan 2027).

**Unit L.6 — Season Obituaries (elimination eulogies).**
When a team is mathematically eliminated, the Writer's Room pitches an affectionate obituary — the Voice Profile's "the league remembers mistakes and brings them back up at the worst possible moment, affectionately" as a genre. Pure substrate-derivable; pitch-docket artifact class via W.4; in-season delight with zero consent surface. Elimination is a derived fact from standings math — deterministic, not predictive.

**Unit L.7 — Tale of the Tape (pre-matchup historical hype).**
Before marquee matchups (rivalry games, playoff games, first-place collisions), a hype piece built from **historical facts only**: series record, streaks, largest margins, last meeting, all-time playoff history between the pair. F1's substrate, deployed at the moment of maximum anticipation.
- **Requires a short boundary memo first (Fable):** history deployed pre-game is admissible; odds, projections, win probabilities, and "keys to the game" are not. The memo draws the line once so every Tale of the Tape inherits it. The constitution bans prediction; it does not ban anticipation.

**Unit L.8 — The Gazette (era-styled front pages) + the Almanac (the printed book).**
- **Gazette:** newspaper-front-page rendering class — championship editions, heist editions ("TROPHY STOLEN IN BROAD DAYLIGHT"), draft-day editions. The most shareable artifact class available; renders from approved content only; rides E1.5a's print channel + W.2's design language. OG/social cards inherit the treatment.
- **Almanac:** the annual printed league yearbook — championship roll, season chronicle, draft history, rivalry pages, Hall of Shame, awards, the Gazette front pages as section dividers. Generated print-ready from the deterministic engine; handed out at the draft. The ultimate Artisan-frame artifact and the natural revenue shape for the eventual platform (groups buy the book). First edition target: 2026 season retrospective, printed before the 2027 draft.

**Unit L.9 — The Commissioner's Ledger (governance lore).**
The league's rules, amendments over time, disputes and rulings — preserved as memory. Every long-running league has legendary rule fights; preserving the ruling, the dissent, and the aftermath is lore of the highest order, and it composts naturally into Historian Interview prompts. Light surface: append-only rulings entries (commissioner-ratified), rendered as a leather-bound ledger in the clubhouse scene. Low priority, high charm; bundle with a W.2 application session.

**Unit L.10 — The Legacy Guarantee (portability + succession).**
The Permanence moat made concrete: (a) **portable archive export** — the league's complete memory (facts, artifacts, testimony, media manifests) in a documented, self-verifying format the founder can hold independent of any platform including SquadVault itself; (b) **succession provisions** — a documented commissioner-handoff path (the founding session re-run mechanism B2 is the seed) so the memory survives its keeper. This is also the marketing sentence for every future vertical: *"Your twenty years don't belong to a platform. They belong to you."*
- Route: (a) is an engineering unit (Opus, off-season-eligible — the archive layout + docket system already approximate it; formalize the manifest + integrity proof); (b) is an operational-scenarios addendum (doc session).

---

# PART 5 — MARKET POSITION REGISTER (named, governed, mostly post-closure)

Recorded so the Closure Memo session inherits a real Phase 12 option set; nothing here is authorized work before closure except as noted.

- **Category claim:** SquadVault defines **Verified Memory** — AI-assisted, provenance-governed, human-approved community memory. The anti-category positioning ("slow fantasy": no feeds, no badges, no predictions, no attention extraction) is itself the differentiator in a market of engagement machines; the Data Ethics memo already contains this language — productize it when a second league onboards.
- **Phase 12 candidate slate (for the Closure Memo to adjudicate):** L.2 Ask the Historian (lead candidate); claim-level tappable provenance as a general artifact feature; audio renderings (league radio); the live auction-draft companion (sibling product; deterministic state-machine sketch on file); multi-league onboarding (the founding session + Historian Interviews ARE the onboarding product); the Almanac as a revenue artifact; **vertical expansion thesis: more kinds of remembered communities (campaigns, golf trips, rec leagues, families), not more fantasy platforms** — the archive format (L.10) is what generalizes, the fantasy module is what proved it.
- **The moat math for diligence:** Trust took a year of falsification discipline (non-replicable by announcement); Voice compounds with time-in-community (non-replicable by capital); Permanence inverts the industry's lock-in incentive (non-replicable without abandoning the standard business model). All three are already partially evidenced in the repo of record.

---

# PART 6 — CONSOLIDATED DECISION REGISTER

| # | Decision | Recommendation |
|---|---|---|
| D-A | Pre-commit pytest subset | No — ruff only |
| D-B | E1.4 fresh-gen n + spend cap | n=24–36; explicit cap |
| D-C | `promote-version` now vs after season | Defer |
| D-D | Project-knowledge curation | Yes; founder picks retained set |
| D-E | Owner-lineage prose on 0010 | No; stay silent |
| D-F | Formatting gate: verifier category vs standalone lint | Standalone |
| D-G | A/V Room v1 media scope | Photo+video read; photo-first tooling |
| D-H | Ratify named aesthetic pre-W.2-application | Founder session |
| D-I | First pitch-docket class | Throwbacks |
| D-J | Trophy taxonomy ratification pre-W.5-spec | Founder enumerates real trophies/rules |
| D-K | Custody backfill depth | Honest gaps over speculated completeness |
| D-L | Warmth/Lore track entry | W.7 + W.6 immediately; W.1 first build |
| D-M | E1.5a before vs consuming W.2 | If W.2 runs this summer, consume; else channel-neutral now |
| D-N | Historian Interviews first wave | Pre-draft August sweep |
| D-O | The Vault ship date | **Before 2026 draft — hard calendar anchor** |
| D-P | Awards slate ratification | Founder names the awards from lore |
| D-Q | W.8 placement authority | Communal walls: commissioner; member offices: the member |
| D-R | W.8 decor sourcing | Real corpus artifacts first; original era-evoking ephemera second; copyrighted reproductions never |

# PART 7 — MASTER SEQUENCE (the document of record's one-page answer)

**Now → July:** E1.1 → E1.2 → E1.3 (drift gone, docs true) · W.7 (drift-flag memo) · W.6 (consent governance) · E1.4 (fabrication baseline) · E1.5a (presentation spec).
**July → August (pre-draft):** W.1 A/V Room (build + founder media ingest) · W.2 art direction (addendum, then application begins) · **L.3 The Vault — must be live by draft day** · L.1 Historian Interviews first wave (pre-draft sweep — also the Memorabilia Pipeline's first fuel) · E1.5b formatting gate · W.3 corkboard · W.5 trophy taxonomy ratification + spec chain.
**Season (Sept → Jan):** E2.1 Week-1 revision-point · E2.2 weekly cycles (six consecutive = Phase B exit) · E2.3 onboarding riding W.1 + L.1 · W.4 pitch docket (first class: throwbacks; then L.6 obituaries, L.7 Tale of the Tape post-boundary-memo; W.8 set-dressing pitches as interviews accumulate) · W.5 Mantel build + backfill · E2.4 voice retrospective (~W8) · Gazette first editions at season moments.
**Season's end (Jan):** L.5 Awards Night + L.3 reveal as the Season Finale ceremony · L.8 Almanac first edition into production.
**Post-season (Feb 2027 →):** E3.1 evidence assembly · **E3.2 Phase 11 Closure Memo** — the completion event — adjudicating the Part 5 Phase 12 slate with L.2 Ask the Historian as lead candidate · Almanac delivered at the 2027 draft.

# PART 8 — WHAT THIS DOCUMENT DELIBERATELY DOES NOT DO

No autonomous publication in any form. No measurement of member behavior, ever. No feeds, badges, streak-dopamine, or notification pressure. No predictions, odds, projections, or advice — anticipation yes, prophecy no. No full 3D. No likeness or voice synthesis ahead of W.6. No invented trophy mechanics. No fixed Phase 11 end-date (Roadmap §8.3 binds). No pre-determined Closure Memo outcome. No re-litigation of the falsified context-manipulation levers.

**The shortest honest statement of the whole document:** harden the gates, measure the baseline, give the words their typography — then hang the photos, seal the letters, interview everyone, put the trophies on the mantel with their criminal records, and run the season so well that by Awards Night the league isn't using a product; it's living in its own memory. Trust is built. Voice and Permanence are next. The product completes by being used — and becomes defining by being loved.
