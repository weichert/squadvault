SquadVault — Completion Plan v1.4
Date: 2026-07-05. Supersedes: v1.3 (2026-07-01; retained unmodified, append-only). Authored: DECIDE session, reconciled against HEAD (frontend + engine verified this session), not against memory or prior-plan claims.
1. Why v1.4 exists
v1.3 predates the 2026-07-05 session and is roughly a session behind: it lists W.2 Clubhouse as optional/unbuilt (it shipped), and knows nothing of the Coach Office room, the dual-layer principle, the Trophy Hall, the four generated awards, or the CO v2 increments. v1.4 reconciles what shipped, records the new scope, and — its reason for being — provides the Dual-Layer Room Map: the systematic inventory that answers "does every data view have a planned room, and in what order," honestly triaged so the finish is efficient, timely, and appropriate.
2. What shipped since v1.3 (verify at HEAD)
Engine: 1.7a spec (ce38f23); A8 Manual Source Adapter (07f9e36); 1.7b closing R5 (fcc5279); A9 registered; continuity memo + addenda + runbook kickoff. Frontend: MW.1 middleware honesty; QA.1 vitest harness (6b31abf); CO.3 viewer resolver; RS.1 splash; W.2 Clubhouse room (b63e8da) — the keystone experiential unit, live; Coach Office Room v1 (936a8ee) — live; the dual-layer principle memo (54062e7). Verified live/shipped: A/V Room (W.1), Trophy Room fact page + custody (W.5).
3. What was discovered/designed this session

Four awards (Hammer/Benchwarmer/Clairvoyant/Oracle) are GENERATED engine-side (facts exist) but unread by the frontend → display work, gated on the founder's seed-004 prod apply. The Unbroken Chain is DEFERRED (no generator). The Oracle-exclusion ruling was reversed (append-only): its fact is retrospective, constitution-clean; only sundial art is pending.
The Dual-Layer Presentation Model (54062e7): illustrated rooms are derived presentations of the fact layer; a visible provenance toggle demonstrates the values; set-piece triage reserves rooms for emotional scoring chances; nostalgic accretion makes rooms live over time.
Landed briefs, successor-executable: Trophy Illustrated Display (064716a) + generated-awards amendment; Trophy Hall room (36f8ca3, which folds in the display work + builds the provenance toggle first); CO v2 Personal Media (4bf19f1), Team Identity (ac4ad98), Ambient State (30fb38f); CO Room v1 (6474cdb).

4. THE DUAL-LAYER ROOM MAP
Every member-facing data view, classified by surface class (SET-PIECE = full illustrated room + provenance toggle; HYBRID = functional with emotional accent; ADMIN = clean functional, no room by design), with room status and nostalgic payload. Per the principle memo: restraint everywhere except where impact is earned.
SET-PIECE surfaces (rooms):

Clubhouse — data: n/a (hub) · room: SHIPPED (b63e8da) · payload: corkboard notes, answering-machine voicemails, league lore (accretion) · toggle: retrofit (follow-on).
Coach Office — data: shipped (trophies/rings/records/nameplate) · room: SHIPPED v1 (936a8ee); v2 briefed (photos 4bf19f1, logo ac4ad98, ambient 30fb38f) · payload: member photos, team logo, board notes · toggle: retrofit (follow-on).
Trophy Hall — data: shipped (W.5 + custody) · room: BRIEFED (36f8ca3), builds toggle FIRST · payload: member championship reflections (later) · toggle: PRIMARY BUILD.
Hall of Fame & Shame (Phase 11 A1) — data: pure consumer of canonical data (worst seasons, losing streaks, blowouts, the "Forget it!!!" moments) · room: PLANNED, unbriefed · payload: member-nominated shame moments (highest nostalgic fit) · toggle: yes. Highest artisan-fit surface not yet briefed.

HYBRID surfaces (functional + accent):

Members directory · Archive / Championship Timeline (A3) · Draft History Vault (A2) · H2H rivalry table · trade lore — data-forward, light emotional accent; candidate for room-accents mid-season, not full rooms pre-season.

ADMIN surfaces (clean, no room, by design):

Consent · sign-in · admin panels · the raw provenance/data view itself (which the toggle reveals everywhere). Dressing these up would harm them; the toggle keeps data reachable, so no room is needed.

5. Sequencing — honest triage against the calendar
Before the season (make the Draft-Weekend reveal land): the set-piece rooms — Clubhouse (done), Coach Office v1 (done), Trophy Hall (execute this — the strongest pre-season surface: display over frozen data, folds in the generated awards, builds the toggle). Founder acts that gate these: apply seed 004 to prod; finish trophy art (knockouts done, Oracle sundial + gap renders + variant picks + Clairvoyant-imagery ruling).
Mid-season / post-launch (richer with time + members): Hall of Fame & Shame (brief when the weekly rhythm is stable); CO v2 increments (photos/logo/ambient); provenance-toggle retrofit to Clubhouse/Office; nostalgic-accretion features; Ask-PFL (Phase 12, needs its constitutional adjudication first); Writer's Room (W.4, stays Window D — do not pull forward). Hybrid-surface room-accents.
Never rooms: the admin surfaces (§4).
6. The open-work register (reconciled against the record)
Founder acts: post the league note; apply seed 004; finish trophy art + the two art rulings (Clairvoyant imagery, Oracle/Cavallini sundial); nine Draft-Weekend invites; project-prompt one-line clone edit; stale-clone deletion. DECIDE-owed (unauthored): Ask-PFL constitutional adjudication (before any query brief); Writer's Room historical PoC; Hall of Fame & Shame brief (when rhythm stable). Engine: A9 (2018 de-contamination); the Unbroken Chain generator (if ever). Hygiene (A4-class): scripts/ lint tier (D-R), STATE trim (D-T), A/V doc staleness, likeness_derived partial toggle.
7. What v1.4 deliberately does NOT do
It does not brief every planned room now (silence over speculation, applied to scope). It records the map and sequences it; the rooms are briefed as their windows arrive. The season can run on what is shipped — the engine is trustworthy and live. The finish is a cathedral built in the right order, not all at once.
