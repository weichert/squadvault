# OBSERVATIONS — Frontend-Inclusive Gap Analysis

**Date:** 2026-05-29
**Author:** Steve, with Claude
**Status:** Discovery memo. Not promoted to `docs/` Map. Sits in `_observations/`
as the cross-repo snapshot and continuity surface produced by this session.
**Purpose:** Build a *deliberately complete* picture of where the SquadVault
project sits across both repos (engine + frontend), surface gaps that have
accumulated because continuity mechanisms have been engine-leaning, and capture
the ideas and open decisions that risk loss between conversations.
**Trigger:** Steve's stated intent to keep moving on frontend development, with
the worry that "we move from one conversation to another" and things get lost.

This memo is observation-only. It does not change architecture, code, gates,
or doctrine. It is a registry of state and a capture surface for ideas that
have surfaced informally and could otherwise fall out.

---

## 1. Scope and shape

Prior session briefs and most observations have been engine-centric. The
frontend repo (`weichert/squadvault-frontend`) has its own commit history and
its own milestone cadence; its state is largely uncovered by the existing
continuity surfaces. This memo's job is to write the missing half down.

Sections 2–4 inventory state. Section 5 names the asymmetries. Sections 6–8
inventory open work streams. Section 9 captures cross-cutting open decisions.
Section 10 lays out dependencies. Section 11 names the continuity mechanisms
this memo recommends going forward. Section 12 suggests the next session's
opening move.

---

## 2. Engine state (`weichert/squadvault`)

### 2.1 Repo position
- HEAD: `d13bdbb` — `docs(observations): Writer's Room vision and historical
  calibration memo`
- Branch: `main`, clean working tree, pushed.
- Test baseline: 2314 passed, 2 skipped across all three `prove_ci` pytest
  runs. Drift hashes match.
- Ruff: zero errors in `src/`.
- Mypy: zero errors across `src/squadvault/core/`.
- Pre-commit hooks active: banner gate, no-xtrace, repo-root allowlist
  (exactly 5 files), `docs/` Map registration gate.

### 2.2 Architecture summary
- Canonical event store (SQLite at `.local_squadvault.sqlite`).
- Append-only ledger; facts immutable.
- Niche-agnostic `core/` (no fantasy vocabulary).
- Fantasy module is a layer on top.
- Recap generation pipeline with selection layer, prompt construction,
  verifier, and approval state machine.
- Filesystem archive surfaces at `archive/<surface>/` for A1/A2/A3.

### 2.3 Phase 11 progress (operationally live)
- E1 (Weekly Recap Distribution Surface) — live.
- A1 (Hall of Fame & Shame) — live.
- A2 (Draft History Vault) — live; template v1.0 validated against 3
  instances; promotion-eligible.
- A3 (Championship Timeline) — live.
- E2-light (Weekly Recap Archive) — live (per Map v1.7 provisional list).
- F1 (Rivalry Chronicle) — substrate exists; surface deferred per Milestone
  3 brief §7.

### 2.4 Engine→Supabase bridge (sync layer)
Two distinct sync scripts reflecting two different artifact lifecycles:

- `scripts/sync_to_supabase.py` — DB-state lifecycle. Reads APPROVED rows
  from `recap_artifacts`, writes `(artifacts, artifact_versions, docket_ids)`.
  Idempotent by `engine_artifact_id`; hash-keyed version detection. Covers
  E1 (WEEKLY_RECAP) and F1 (RIVALRY_CHRONICLE_V1).
- `scripts/sync_archive_to_supabase.py` — filesystem-source lifecycle. Reads
  `archive/<surface>/index.md + sub-pages`, concatenates and rewrites
  in-page anchors, derives `approved_at` from `git log`, uses content hash
  for idempotency, writes synthetic ids and dockets like
  `SV-{CLASS}-{YEAR}-{SHORTSHA}`. Covers A1/A2/A3.

Both load `.env.local` via `scripts/_env_bootstrap.py` (commit `3997f13`).

### 2.5 Recent engine commits worth surfacing for frontend planning
- `e6477b0` — `docs(_observations): public artifact audience split` (2026-05-28):
  raised the question of whether the commissioner audit trail should remain
  visible on the public archive surface or be split. Recommendation: Option B
  (split, audit trail visible only on commissioner approve/review surface).
  **Decision deferred.** Implicates frontend rendering of `content_markdown`.
- `2a55fd1` — `docs(_observations): league pages force-dynamic by design`:
  documents the rationale for `export const dynamic = "force-dynamic"` on
  league/office/archive routes. Cross-repo concern: this is engine memo
  about frontend behavior.
- `a5f79f9` — added `sync_archive_to_supabase.py` (Milestone 3 Track A
  archive sync).
- `030039f` — original `sync_to_supabase.py` (Milestone 3 Track A E1/F1
  sync).

### 2.6 Documentation Map v1.7
Currently lives at `docs/SquadVault_Documentation_Map_v1_7.md`. Notable for
frontend planning:
- Tier 1 binding documents include Operational Plan v1.1, Platform &
  Writer's Room Compact v1.0.
- All Phase 11 surface specs (E1/A1/A2/A3/E2-light) are listed as
  *provisional* — `_observations/` resident, not Map-registered, awaiting
  one-cycle-observed + founder election.
- Phase 11 Surface Roadmap (`ba8b58a`) — provisional.
- Surface Admission Test — not yet authored (predecessor state unmet).
- Doctrine-to-Product Translation Table — not yet authored.

---

## 3. Frontend state (`weichert/squadvault-frontend`)

### 3.1 Repo position
- HEAD: `bf6d396` — `fix(ui): opt server Supabase reads out of Next.js Data
  Cache`
- Branch: `main`. Working tree assumed clean (last verified by Steve at end
  of prior session).
- Tech stack: Next.js 14.2.15 (App Router), TypeScript, Tailwind CSS,
  Supabase (auth + DB), `@supabase/ssr`, `@vercel/og`, Upstash Redis
  (rate-limiting), `react-markdown`.

### 3.2 What's built
**Auth + middleware**
- Magic-link login via `/auth/login`.
- `/auth/callback/route.ts` for Supabase OAuth callback.
- `middleware.ts` for edge auth guard.

**Routes (every `page.tsx` and `route.ts`)**
- `/` — landing.
- `/auth/login`, `/auth/callback`.
- `/league/[id]` — community page (LockedRoom when `status='founding'`,
  founding plaque + community shell when `status='active'`).
- `/league/[id]/office` — Commissioner Office approval queue
  (DRAFT/CHANGES_REQUESTED).
- `/league/[id]/approve/[artifactId]` — single artifact review (scroll-to-
  unlock approval).
- `/league/[id]/archive` — archive index across surface classes.
- `/league/[id]/archive/recaps` + `[artifactId]` — E1 weekly recaps.
- `/league/[id]/archive/records` + `[artifactId]` — A1/A2/A3 entries.
- `/api/artifacts/[artifactId]/approve` — POST: transition DRAFT/CR →
  APPROVED.
- `/api/artifacts/[artifactId]/withhold` — POST: transition → WITHHELD.
- `/api/artifacts/[artifactId]/request-changes` — POST: transition →
  CHANGES_REQUESTED.
- `/api/manifest` — PWA manifest per league.
- `/api/og` — OG image generation.

**Components**
- `trust-bar.tsx` — all 4 trust bar variants (CERTIFIED, DEMO, ATTESTED,
  DRAFT).
- `docket-id.tsx` — docket ID display.
- `locked-room.tsx` — pre-activation vault door.
- `artifact-review.tsx` — review surface with scroll-to-unlock and three
  action buttons.

**Supabase schema (frontend-owned migrations)**
- `001_core_schema.sql` (196 LOC): leagues, voice_profiles, franchises,
  artifacts, artifact_versions, approval_events, docket_ids,
  trophy_room_entries, founding_sessions, commissioner_notes, sync_log,
  audit_log.
- `002_constraints_and_triggers.sql` (138 LOC).
- `003_rls_policies.sql` (254 LOC).
- `004_commissioner_email.sql` (15 LOC).
- Seed: `001_pfl_buddies_demo.sql` (126 LOC).

**Governance test runner**
- `scripts/test-governance.ts` — six tests live: G1 (anon cannot retrieve
  unapproved artifacts), G3 (no DELETE policies on any table), G4 (invalid
  state transition rejected at DB layer), G6 (anon cannot read private
  league artifacts), G7 (demo artifact has correct trust bar text), G9
  (trust bar and docket ID on approved artifacts).
- Run via `npm run test:governance`.

### 3.3 Milestone state (per commit log)
- Milestone 0 — Clubhouse scaffold: `2134c0b`.
- Milestone 1 — Supabase schema + auth: `2134c0b`.
- Milestone 2 — Commissioner Office + approval ceremony: `d0402d6`,
  `eda8d39`, `a64704f`, `ad644bd` (G-tests passing).
- Milestone 3 Track B — Archive surfaces (E1/A1/A2/A3): `3466a65`.
- Caching fix: `bf6d396` (current HEAD).

Frontend has reached **Milestone 3 Track B complete**. SETUP.md mentions
Milestones 0+1+2 with "what's next" pointing to Milestone 2 — i.e. the
SETUP.md is stale relative to current code, which is already past
Milestone 3 Track B.

### 3.4 What's NOT built (vs. spec)
- **Commissioner Founding Session (State 3)** — schema row exists
  (`founding_sessions` table, `FoundingSession` TypeScript type). Zero UI.
  No agent prompt. Spec at
  `Clubhouse_Commissioner_Founding_Session_State3_Spec_v1_0.md` is fully
  written; implementation is greenfield.
- **F1 (Rivalry Chronicle) archive surface** — deferred per Milestone 3
  brief §7; `week_index=204510` packed-integer issue noted in audit-split
  memo.
- **Trophy Room** — `trophy_room_entries` table exists in schema; no UI.
- **Charter Member Row / community page hero** — minimal placeholder
  rendering; no full hero component per Design Brief §7.1.
- **Member Office** — Design Brief Part VIII references it as a surface;
  no route exists.
- **Search across archive** — Design Brief §7.2 references it; not built.
- **"This Week in History" callout** — Design Brief §7.2; not built.
- **Voice profile pre-generated examples** — Design Brief Part X open
  decision; not built.
- **Print stylesheet** — Design Brief Part X open decision; not addressed.

### 3.5 Frontend continuity surfaces (what exists today)
- `README.md` (boilerplate `create-next-app` text — stale).
- `SETUP.md` (Milestone 0+1 guide; stale relative to current code).
- No `_observations/` equivalent. No session-brief equivalent. No
  contributor-onboarding equivalent.
- No `CHANGELOG.md`. Commit messages are the only narrative record.

---

## 4. Cross-repo integration surface

### 4.1 Schema contract (the seam)
The frontend's `src/lib/supabase/types.ts` is the *contract* between engine
sync scripts and frontend rendering. Every table the sync scripts write
must match a TypeScript interface here. Notable contracts:

| Table | Engine writer | Frontend reader | Notes |
|---|---|---|---|
| `leagues` | sync scripts (insert if missing) | every league route | canonical_id = MFL league id (e.g. `70985`) |
| `franchises` | sync scripts | community page | charter members, seasons_active |
| `artifacts` | both sync scripts | office, archive, approve routes | approval_state machine |
| `artifact_versions` | both sync scripts | review/render routes | content_markdown |
| `approval_events` | API routes (frontend) | (audit) | append-only |
| `docket_ids` | both sync scripts | trust bar / record entry | unique |
| `voice_profiles` | (TBD: founding session) | community page | scoped per league |
| `founding_sessions` | (TBD: founding session) | (TBD) | State 3 schema present, no UI |
| `trophy_room_entries` | (TBD: commissioner-attested) | (TBD: trophy room UI) | provenance: canonical/attested/demo |
| `commissioner_notes` | (TBD) | (TBD) | append-only |
| `sync_log` | engine sync scripts | (debug) | one row per sync run |
| `audit_log` | API routes | (admin only) | every approval action |

### 4.2 Approval state machine
Lives in DB triggers (engine-defined schema, frontend-owned migration).
States: DRAFT → UNDER_REVIEW → CHANGES_REQUESTED → APPROVED → WITHHELD →
DISTRIBUTED. Transitions enforced by trigger
(`002_constraints_and_triggers.sql`). Frontend API routes
(`approve/withhold/request-changes`) issue the transitions; G4 test verifies
the trigger rejects invalid transitions.

**Cross-repo invariant:** the engine sync writes new artifacts as DRAFT.
The commissioner moves them to APPROVED through the frontend. Distribution
happens via engine script (`distribute_recap.py`). Whether the engine then
*reads back* the Supabase APPROVED state to gate distribution is an open
question — currently the engine governs distribution off its own local DB.

### 4.3 Trust bar string contract
The engine's `sync_to_supabase.py` hardcodes:

    TRUST_BAR_CERTIFIED = "Entered into the Record \u00b7 Source Facts
                           Verified \u00b7 SquadVault"

The frontend's `src/lib/supabase/types.ts` declares:

    TRUST_BAR.CERTIFIED = 'Entered into the Record · Source Facts Verified
                           · SquadVault'

These match on the unicode middle dot, but the original DB default
(`001_core_schema.sql` line ~68) uses pipes. This is a known historical
quirk; the sync layer normalizes to middle-dot for new inserts.

### 4.4 Frontend reads from engine without sync
The `dynamic = "force-dynamic"` declaration on league routes means the
frontend reads live Supabase state on every request. The engine memo
`OBSERVATIONS_2026_05_28_LEAGUE_PAGES_FORCE_DYNAMIC.md` documents the
rationale: synced artifacts must surface without a hard reload.

This is the critical observation: **the engine and frontend are coupled
through Supabase, not through a synchronous API.** Engine sync is push;
frontend rendering is pull. There is no callback the other direction
(except API-issued state transitions writing back to the same Supabase).

### 4.5 The audience split (2026-05-28 memo)
The engine's `rendered_text` field contains *two audience segments*
(commissioner audit trail + league-facing prose) separated by literal
delimiter lines:

    --- SHAREABLE RECAP ---
    [league-facing prose]
    --- END SHAREABLE RECAP ---

The frontend currently does not split these. Recommendation in
`OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md` is Option B:
audit trail visible only on commissioner approve/review surface; public
archive surface shows only the shareable segment. **Decision deferred.**

---

## 5. Cross-repo asymmetry findings (the gaps)

These are the gaps that motivated the question Steve asked. Each is named
plainly here so it can't get lost.

### 5.1 No frontend continuity mechanism
The engine has `_observations/` (139 memos), session briefs, the
Documentation Map, addenda, contracts directory, gate scripts that
self-enforce. The frontend has none of these. Commit messages are the only
narrative trace; SETUP.md is stale; no per-session brief mechanism;
no observation memos. Anything discussed about the frontend in conversation
dies in the chat log if not committed in code.

**Cost:** every frontend-side conversation starts from scratch on context.

### 5.2 Documentation Map is engine-only
The Map (v1.7) registers engine docs, Tier 0–5 documents, Phase 11
surfaces. There is no entry for *any* frontend artifact — not the
Clubhouse Design Brief, not the Founding Session spec, not the migrations,
not the Milestone briefs. The Clubhouse Design Brief is "Plan of Record" by
its own header but is not Map-registered.

**Cost:** the Map's governance model (registration-as-commissioning)
cannot apply to frontend work as currently scoped. Frontend documents are
provisional-by-default with no mechanism for promotion.

### 5.3 Milestone briefs are referenced but not findable
The engine memo `OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md`
cites "Milestone 3 brief §3", "Milestone 3 brief §7", "Milestone 3 brief
§8". These briefs exist somewhere (presumably in Steve's notes or a chat
log) but are not in either repo. SETUP.md mentions Milestones 0/1/2;
commit messages mention Milestone 3 Track B; no document enumerates the
full milestone set.

**Cost:** the milestone roadmap is partly in code commits, partly in chat
history, partly in the Design Brief, partly in observation memos. No
single ordered list exists.

### 5.4 Commissioner Founding Session is fully specced, zero implemented
`Clubhouse_Commissioner_Founding_Session_State3_Spec_v1_0.md` is detailed:
opening sequence, voice calibration profiles, three outputs, edge cases,
session state schema. Implementation requires: Supabase schema
finalization (some present, P1 in spec), agent prompt construction (P1),
voice profile prose generation (P1), office brief structured generation
(P1), Review Room trigger (P2), PRE_DIGITAL_HISTORY flag flow (P2),
individual member onboarding adaptation (P2), Season 1 review trigger
(P3).

**Cost:** this is the most consequential frontend surface yet to be built
(per the spec itself: "the most consequential conversation the platform
ever has with a group"). It is greenfield. It is the State 3 founder
experience.

### 5.5 Vision-memo themes have no frontend translation
The 2026-05-29 vision memo articulates the Writer's Room as the product
and the substrate as precondition. It names the host/moderator as a live
design option (Q6, Q7). None of these vision items have a frontend
companion document. The frontend has been built per Design Brief v1.0,
which predates the vision memo.

**Cost:** the next round of frontend work risks being out of sync with
the vision unless the connection is made deliberately. The host idea, the
onboarding-as-apprenticeship framing, and the historical calibration plan
each have frontend implications.

### 5.6 The audience-split decision blocks a frontend feature
`OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md` recommends
Option B but explicitly defers the decision. As long as it's deferred,
the public archive surface renders both audit trail and shareable prose to
all members. This is a known cosmetic-and-trust shortfall.

### 5.7 F1 (Rivalry Chronicle) is dual-stuck
- Engine: substrate exists, surface deferred.
- Frontend: surface card present in archive index with `href: null`
  ("Surface in preparation").
- Sync: writes F1 rows but with `week_index=204510` packed integer and
  unparseable docket text.

All three repos / surfaces have a "wait" on F1. No single owner is
unblocked.

### 5.8 Sync scripts are not automated
Both sync scripts are manual invocations. There is no cron, no CI hook, no
webhook between engine and Supabase. The engine writes archive directories
locally; Steve runs the sync script; rows appear in Supabase; the frontend
renders them on next request (no caching). This is correct for now (every
sync is governance-bearing) but is a known operational manual step.

### 5.9 SETUP.md staleness
The frontend's SETUP.md describes Milestones 0+1 setup. Current code is
past Milestone 3 Track B. SETUP.md's "What's next (Milestone 2)" section
describes already-built work. A new contributor (or future-Claude) reading
SETUP.md would not know the actual current state.

### 5.10 No frontend test baseline equivalent
Engine has `prove_ci.sh` and a 2314-test pytest baseline. Frontend has six
G-tests, run on-demand. No CI configuration is committed (no
`.github/workflows/`). No equivalent of `prove_ci` exists. Type-check
(`npm run type-check`) and governance tests exist as scripts but are not
gated.

### 5.11 No cross-repo synchronization mechanism
Schema is owned by frontend migrations. Engine sync scripts depend on
that schema. If the engine adds a field, the frontend migration must add
a column; if the frontend changes a column, the engine sync must reflect
it. There is no contract test, no schema versioning across repos, no
documented protocol. Today this works because Steve is the only writer to
both repos.

---

## 6. Open work streams — frontend

Ordered roughly by readiness. Each is named without commitment.

### 6.1 Milestone 4 (next major)
- F1 Rivalry Chronicle surface — once the engine surface ships and the
  packed-week-index decoding decision is made. (Cross-stream: §5.7.)
- Or: Trophy Room UI — schema exists, no UI. Could ship independently of
  engine work.

### 6.2 Commissioner Founding Session (State 3)
P1 implementation items from the spec §12. Greenfield. Touches frontend
(chat UI, voice calibration cards, three-output approval flow), Supabase
schema (already present), and engine (no engine work required for the
session itself; engine consumes the Voice Profile output).

### 6.3 Audience-split rendering decision implementation
Decide §4.5 / §5.6 first, then split the rendering. Small mechanical
change, but governance-bearing.

### 6.4 SETUP.md / README rewrite
SETUP.md is stale at Milestones 0+1. A current-state SETUP would describe
local dev across both repos, the sync workflow, the schema link, the
governance test set. Could be paired with a frontend `_observations/`
directory creation (§11).

### 6.5 Trophy Room UI
Schema is ready (`trophy_room_entries`, `provenance` enum). UI is missing.
Design Brief §7 covers the surface. Could be Milestone 5 or sequenced
elsewhere.

### 6.6 Member Office
Design Brief Part VIII references it; not built. Member-facing companion
to Commissioner Office.

### 6.7 Search across archive
Design Brief §7.2. Not built. Lower priority by Design Brief itself
(chronological is the default).

### 6.8 "This Week in History" callout
Design Brief §7.2. Cross-season feature. Requires accumulated history
(historical calibration item, §7.3 below).

### 6.9 Print stylesheet, PWA manifest extension, OG image refinements
Design Brief Part X open decisions. Each is small in isolation, but each
is a deliberate decision rather than a default.

### 6.10 Frontend CI
GitHub Actions configuration: type-check, governance tests, build. Matches
the engine's `prove_ci.sh` model in spirit. Currently nothing runs
automatically.

### 6.11 Light mode toggle
Design Brief Part X open decision. Launch dark-only is the current state;
toggle is a deferred decision.

---

## 7. Open work streams — engine that gates or enables frontend

### 7.1 F1 surface promotion (gates frontend §6.1)
F1 surface deferred per Milestone 3 brief §7. Until engine promotes F1
surface, frontend cannot ship F1 archive UI cleanly. (Packed-week-index
decision is a separable sub-decision.)

### 7.2 Audience-split decision (gates frontend §6.3)
`OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md` recommended
Option B; decision deferred. Until landed as a doctrinal decision, the
frontend can't confidently implement the split.

### 7.3 Historical calibration pass (enables frontend §6.8 and onboarding)
Vision memo §5.2: scoped first historical pass on one season. Outputs
voice-calibration feedback, which feeds the onboarding design (vision
§5.4), which is the State 3 Founding Session (frontend §6.2). Also
generates the cross-season material that "This Week in History" needs.

### 7.4 Voice Profile generation (gates Founding Session)
The State 3 spec produces a `League Voice Profile` (output 3). The engine
needs to provide the generation surface (Claude API call producing prose
profile from calibration selection). Spec §12 lists this as P1 owned by
"AI/Product."

### 7.5 NFL canonical event store architectural pass
Vision memo §5.1. Parallel event store for NFL storylines. Not part of
current Phase 11 work. Real scope.

---

## 8. Open work streams — engine independent of frontend

These exist in userMemories and prior briefs. Listed for completeness;
none of them block frontend forward motion.

### 8.1 Phase 11 closure-and-tidy
- A3 selection-prep (next in the surface sequence).
- Template promotion (A2 template v1.0 is promotion-eligible).
- Surface Admission Test (predecessor state unmet; one content-class
  admission attempted required; not yet authored).
- Phase 11 Closure Memo (6 certifications per §8.4).

### 8.2 Documentation Map v1.6/v1.7 gap-audit resolution
M1–M5 meta-questions pending deliberate resolution. v1.7 has been written;
v1.6 was the intermediate. Map drift items resolved in v1.7 absorption.

### 8.3 A2 anchor revocation correction
Memo correction + test rename:
`test_cavallini_mahomes_2018_qb_anchor_regression` should reflect the
actual A2 record ($76 Barkley by Cavallini in 2019, not Mahomes 2018).

### 8.4 Seasons-count drift sweep
A1 Step 1 §4.2 (17→16 digital era); A2 selection-prep §10.1 (16→8
structural-read); A2 Step 1 §4.1 (8→7 empirical due to 2021 zero
DRAFT_PICK events).

### 8.5 Vision-memo direction work
NFL canonical event store, scoped historical pass, bracket vs in-the-moment
registers, onboarding design, host customization (Q6), host surfaces (Q7).
Q7 ideas (group chat, AMAs, mini-games, visual host) are explicitly
capture-light — not in active scope.

---

## 9. Cross-cutting open decisions

These are decisions that gate or shape multiple streams. Decision-deferred
status means they're known-unresolved.

### 9.1 Audience split (engine memo, 2026-05-28)
Option A vs B vs other. Recommendation: B. Decision: deferred.
Affects: frontend §6.3, sync metadata.

### 9.2 F1 surface readiness
When does F1 substrate ship a surface? Engine deferred. Frontend stub
present.

### 9.3 Founding Session implementation sequencing
The State 3 spec is complete. Implementation has not started. Should it
happen before, after, or alongside other Milestone 4 work? The spec
implies "before any new league onboards" — but PFL Buddies is the only
league, and they're already past founding. So the question is whether to
build it for the *next* league (multi-tenant story) or as a tested-on-
hypothetical-second-league rehearsal of the State 3 experience.

### 9.4 Vision-memo promotion to `docs/`
The vision memo sits in `_observations/`. No promotion mechanism is
specified until Documentation Map v1.6 (or v1.7) author a registration
gate. Currently the registration-as-commissioning rule exists; the vision
memo has not been put through it.

### 9.5 Host customization (Q6 in vision memo)
Pick / Build / Accrete. Sequenced after onboarding architecture and
accumulated historical material. Frontend implications: how does a host
manifest in the UI? Is there a "host" component? Does the host have a
photo, an avatar, a name?

### 9.6 Light mode (Design Brief Part X)
Dark-only is current. Toggle deferred.

### 9.7 OG image generation strategy (Design Brief Part X)
Static per-league vs dynamic per-artifact. Was supposed to be decided
before Milestone 3 ships. Milestone 3 has shipped. Decision status:
inferred from `/api/og/route.tsx` — appears to be a per-league dynamic
endpoint. Worth confirming.

### 9.8 Voice profile example generation (Design Brief Part X)
Pre-generated static vs live-generated on demand. Decision: should have
been made for Founding Session §6.2 implementation.

### 9.9 Approval stamp visual (Design Brief Part X)
Custom SVG seal vs checkmark + rule. Currently implemented (commits
`eda8d39` + `a64704f`). Decision was made implicitly. Worth a one-line
ratification.

### 9.10 PWA manifest (Design Brief Part X)
Implementation exists at `/api/manifest/route.ts`. Decision was made.
Worth a one-line ratification.

### 9.11 Print stylesheet (Design Brief Part X)
Low effort per the brief. Decision-deferred.

### 9.12 Keyboard navigation depth (Design Brief Part X)
Approval UX has tab/space/enter. Whether to extend to archive: deferred.

---

## 10. Dependencies and ordering

The following arrows show what blocks what. Read "A → B" as "A unblocks
B" or "A is the precondition for B".

```
Phase 11 surface stability (live)
    → §6.1 F1 surface (gated by §7.1 + §9.2)
    → §6.5 Trophy Room UI (independent; can ship)

Historical calibration §7.3
    → onboarding design (vision §5.4)
    → §6.2 Founding Session implementation
    → §6.8 This Week in History
    → host design Q6 (§9.5)

Audience-split decision §9.1
    → §6.3 split rendering
    → cosmetic-trust shortfall closure

Founding Session §6.2
    ↰ Voice Profile generation §7.4
    ↰ Founding Artifact prompt (engine; spec §12 P1)
    ↰ Office Brief structured generation (engine; spec §12 P1)
    ↰ frontend chat UI + voice calibration cards + three-output approval

Cross-repo continuity §11
    → all future cross-session work
    (no blocker; can ship in parallel)
```

Two key observations:

1. **The shortest path to high-value frontend work is the audience-split
   implementation (§6.3) and/or Trophy Room UI (§6.5).** Neither requires
   engine work. Audience-split needs the decision (§9.1) first.

2. **The largest frontend work is the Founding Session (§6.2), and it
   has the longest dependency chain** — historical calibration → onboarding
   design → implementation. Doing it now without the calibration pass means
   building a State 3 surface against the current Voice Profile, which is
   PFL Buddies' Profile — fine for testing but doesn't exercise the
   multi-niche-tonal flexibility the vision memo names as the core claim.

---

## 11. Continuity mechanisms — recommendation

The asymmetry findings (§5) point to a structural lack of frontend
continuity surfaces. This section proposes specific mechanisms that mirror
what exists engine-side. None of these requires a Map amendment; they are
working-process additions.

### 11.1 Frontend `_observations/` directory
Mirror the engine's pattern. Memos for: decisions made, observations
captured, milestone briefs preserved, audit-style findings. Same naming
convention: `OBSERVATIONS_YYYY_MM_DD_*.md`.

### 11.2 Frontend session-brief mechanism
At end of any session that touches frontend, produce a brief similar to
what the engine produces, sitting in the frontend repo's `_observations/`.

### 11.3 Milestone roadmap document
Single ordered file at the frontend repo root or in `_observations/`,
enumerating Milestones 0–N with their commit refs and current state.
Eliminates the "where are the milestone briefs?" question (§5.3).

### 11.4 SETUP.md rewrite
Replace stale Milestone 0/1 content with current-state setup that crosses
both repos. Owners, paths, env, sync workflow, governance gates.

### 11.5 Cross-repo schema-contract document
A single document — could live in either repo — that names the schema
contract from §4.1, lists the writer/reader for each table, and warns
about coupling. Future schema changes register here. Could be a
candidate for Tier 2 Contract Card status if the Map ever absorbs
frontend.

### 11.6 README rewrite (frontend)
The frontend README is `create-next-app` boilerplate. Replace with one
that names the product, links the Design Brief, and points to SETUP.md.

### 11.7 GitHub Actions CI (frontend)
Type-check + governance tests + build. Matches engine `prove_ci`
discipline. Stops drift between local and prod.

### 11.8 This memo as a recurring artifact
A gap-analysis memo of this shape, written at deliberate intervals (every
~10 sessions? every milestone close?), keeps cross-repo state visible.
This is the prototype.

---

## 12. Suggested next session opening

Given that Steve has explicitly named the goal as forward motion on the
frontend, and the gap analysis (§5–§11) is now captured, the next session
has these candidate moves. None is the default; the call remains Steve's.

### 12.1 Short-path frontend wins
- **Audience-split decision + implementation (§9.1 + §6.3)**: requires
  Steve's call on Option A/B/other; then a small frontend PR. Closes a
  known trust shortfall.
- **Trophy Room UI (§6.5)**: schema is ready; no engine dependency.
- **SETUP.md rewrite (§11.4)**: low-risk, high-orientation-value.

### 12.2 Continuity-first work
- **Stand up frontend `_observations/` + this memo's mechanical
  follow-ons (§11.1–§11.6)**: takes one focused session; pays off across
  every future session.
- **Cross-repo schema-contract document (§11.5)**: produces the artifact
  §5.11 needs.

### 12.3 Vision-aligned work
- **Begin Founding Session (§6.2)**: large, but it's the surface the
  product needs for multi-tenant. PFL Buddies is past founding, so this
  is necessarily built against a hypothetical second league.
- **Scoped historical calibration pass (vision §7.3)**: one season,
  weekly recaps with NFL storylines. Engine work primarily, but the
  output feeds frontend onboarding design.

### 12.4 Cross-cutting cleanup
- **Resolve the open decisions in §9** as a batch. Each is a yes/no/defer
  call; doing them together prevents them from accumulating as drag.

### 12.5 The audit-and-stabilize move
- **Promote this memo to `_observations/` in the engine repo, mirror the
  relevant sections to the frontend repo (once §11.1 stands up), and
  ratify which open decisions are still deferred.** This converts the
  memo from a snapshot into a state-marker that future sessions resume
  from.

---

## 13. What this document is and is not

### 13.1 Is
- A snapshot of state as of `d13bdbb` (engine) + `bf6d396` (frontend).
- A registry of the open work streams across both repos.
- A capture surface for ideas surfaced in this session that would
  otherwise be lost.
- An observation memo, per the engine's existing observation-memo
  convention.

### 13.2 Is not
- A spec. It does not specify what to build.
- A roadmap. It does not order or commit work.
- A doctrinal document. It does not bind decisions; the open decisions in
  §9 remain open.
- Map-registered. Sits in `_observations/`.

### 13.3 Open promotion path
If §11.5 (cross-repo schema-contract document) is authored as a Contract
Card and the Map (v1.8?) extends registration to frontend artifacts, the
schema contract could be promoted to Tier 2. The Design Brief itself is a
candidate for Tier 1 binding-trust document status if it goes through
registration. None of this is required for the memo to do its job.

---

## 14. Reading list for cold future-you

In likely-relevant order if a new session opens on frontend work:

1. This memo.
2. The engine vision memo
   (`OBSERVATIONS_2026_05_29_WRITERS_ROOM_VISION_AND_HISTORICAL_CALIBRATION.md`).
3. `SquadVault_Clubhouse_Design_Brief_v1_0.docx` (frontend authoritative
   design source).
4. `Clubhouse_Commissioner_Founding_Session_State3_Spec_v1_0.md` (the
   biggest unbuilt surface).
5. `SquadVault_First_90_Days_Playbook.md` (operating cadence; relevant
   when Frontend distribution touches engine flow).
6. `OBSERVATIONS_2026_05_28_PUBLIC_ARTIFACT_AUDIENCE_SPLIT.md` (the
   deferred decision affecting the next short-path frontend win).
7. Frontend `SETUP.md` (stale but the only existing setup document; to
   be replaced per §11.4).
8. Frontend `src/lib/supabase/types.ts` (the schema contract; ground
   truth for cross-repo coupling).

---

*Filing: `_observations/OBSERVATIONS_2026_05_29_FRONTEND_INCLUSIVE_GAP_ANALYSIS.md`*
*(engine repo). Sibling to the day's vision memo. Observation-only; no Map
registration; no code or schema change.*
