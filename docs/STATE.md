# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter section 4 (amended v1.1, 2026-06-10). Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- W.1 (A/V Room) Increment 1 MERGED + PROVEN + DISCHARGED (frontend `65da2e6`, PR #2; foundation
  `2cd9f17`, PR #1, live on Supabase - tables+RLS, `league-media` private, storage policy; five
  `/api/av-room/*` routes + ingest/display; G12-15 assert RLS 42501; click-through proven end-to-end).
  Video-ingest hardening D1/D2/D3 MERGED (frontend PR #6 `2367479`, see Discharged) - poster shows;
  PLAYBACK SHIPPED via D-W1-A voice-attestation class (DISCHARGED 2026-06-12, see Discharged).
  Chain RATIFIED+FILED 2026-06-10 (SAT #1; D-W1-1..6; 7.2 on card). Inc 2 (member) gated E2.3.

## Open units (Document of Record v2.1, by ID; descriptions in-repo in the DoR)

- E-cluster: E1.6 (E1.7 DISCHARGED-NATIVE via the W.1 chain). W-cluster: W.1 (Inc 1 DISCHARGED;
  open = video increment + Inc 2), W.2, W.3, W.4, W.5, W.8. L-cluster: L.1-L.10.
- W.1 open work (on the proven Inc 1 foundation): (a) hardening + large-file ingest (D-W1-V1=remedy B)
  + ingest ergonomics (D0-D6) BUILT + MERGED + **DISCHARGED 2026-06-11** (see Discharged). D-W1-A
  voice-attestation class + gated playback DISCHARGED 2026-06-12 (see Discharged); D-W1-A6 DISCHARGED 2026-06-12 (see Discharged); next planning input = E2.3-before-Tahoe sequencing (founder brings the 2026 draft weekend date). Ingest rounds 2-4 COMPLETE + DISCHARGED (PRs #13-#20; #14 auto-closed, #17/#20 docs; frontend main `b2884d7`; migrations 011-014 live; gov 115/0; curator's-bench feature ledger in frontend ROADMAP).
  (b) Inc 2 (member captions/marginalia/self-tag) gated E2.3 - first live 2a-silence (no linked member_user_id; spec 8.1; commish id works).
  (c) Two ingest-extension candidates REGISTERED + PARKED (Google Photos Picker import; EXIF date-proposal, build gated on a recorded-metadata decision note) - trigger = first real shoebox session; `..._W1_INGEST_EXTENSION_CANDIDATES.md`.
- W.6 follow-ups: (1) 7.1 doc-note FILED (frontend `248895c`); (2) commissioner read-only "at
  the gates" DEFERRED to first consumer (W.1/W.4/W.8); (3) auth-session governance tests -
  follow-up. Binding (7.2): future chains declare categories-read / gate / revocation.
- D-SEQ TAHOE SEQUENCING RULED 2026-06-12 (Fable DECIDE; `..._DSEQ_TAHOE_SEQUENCING_RULING.md`): draft weekend end-of-Aug 2026 (exact date pending), ~11 wk runway, draft inside Phase 11 closure horizon. DOCKET in order: E2.3-minimal (magic-link + member_user_id->canonical_franchise + first 2a-silence) -> L.3 The Vault (D-O anchor) -> L.1 first wave (Aug sweep, D-N) -> W.1 Inc 2. Overflow only: W.2/W.3/W.5-tax. Runbook trigger ~Aug 1 provisional (pins on date). L.3 clock opens at E2.3-min (~mid-July), reveal at draft table. D-H aesthetic session admissible (screening-room A/V -> Design Brief v2 Addendum). D-SEQ-6 registered to W.4 (corpus-in-artifact = section-candidate; consent-scope ruling required: in-room vs republication). Carry-forwards (backfill v2, byte-twin, HDR recipe v2, sign-route) stay Deferred.
- D-SEQ DATE PINNED 2026-06-18 (founder-ratified): draft weekend = 2026-08-15; supersedes "end-of-Aug, exact date pending" in the ruling line above. Runway ~8.3 wk from pin / ~9 wk from ruling e908863. D-SEQ-3 runbook trigger PINS 2026-07-18 (~4 wk prior; ~30 days out) - no longer "~Aug 1 provisional", still PARKED until trigger. D-SEQ-4 L.3 collection compresses to ~4-4.5 wk (opens at E2.3-min ~mid-July, reveal at draft table 08-15). Docket order unchanged; fits runway. Draft inside Phase 11 closure horizon (NFL Wk 1 ~09-08).

## Deferred (do not pick up until trigger)

- FAAB residual gate (fabrication instruction-resistant): trigger = a deterministic post-gen gate stripping any FAAB figure not on the canonical per-player allowlist. TRIAGE 2026-06-12: prior unratified Opus build preserved at tag `archive/faab-gate-unratified-064a2c0` (built 2026-06-10, no brief; memo-recorded D-G1/D-G2 lack DECIDE provenance) - reference material only, NOT a merge candidate (38 behind); re-adjudicate D-G decisions at trigger. Remote branch `claude/faab-gate-j5ck4m` deleted.
- E1.6 (`promote-version`): D-C DEFER; trigger = live-season (E2.2) pick among regenerations; Type A scaffold `version_presentation_navigation_v1.py` exists, UI unbuilt.
- Draft Weekend protocol (parked RUNBOOK, not software): live hour permanently OUT OF SCOPE (commodity Zoom; live-stream infra anti-thesis); SquadVault owes everything around it - same-weekend ingest (PR #11/#10), marginalia=Inc 2 (E2.3), L.3 letters (Aug clock), consent machinery already shaped. Deliverable = one-page runbook. Trigger ~4 weeks before the 2026 draft. `..._DRAFT_WEEKEND_PROTOCOL.md`.

## Discharged items (with hashes)

- D-W1-A6 playback rendition DISCHARGED 2026-06-12: ratified in Fable DECIDE session (D-W1-A6-1..5 as presented; mechanism work under invariant 6.9, specification not amendment); ruling memo frontend `1379739`; built PR #22 (`cb04b02` sign-route rendition-else-original; `4509397` client-direct rendition-grant + UI; `6f2204b` A6-4 guard; `b8c3cd2` CSP media-src; `1e9b250`+`93db8aa` quick-look portrait bounding; `5113b41` close-out), merged frontend main `8cd2474`. No new table/RLS; gov 116/0 (no G21). MAJOR RE-ATTRIBUTION: a missing CSP media-src directive was the ENTIRE playback blocker since D-W1-A, all browsers - the HEVC premise narrows to member reach (mixed hardware), the content-type theory is dead (header OBSERVED verbatim `video/quicktime`; stored originals correctly typed; A6-4 guard kept as belt-and-braces), and the D-W1-A Safari glyph re-attributes to CSP. RUNWAY OBSERVED: rendition-absent fallback signed the original (step 0); post-CSP-fix the HEVC original played in Chrome-on-macOS with sound; SCRUB-SEEK confirmed via 206 range requests (last D-W1-A flag CLOSED; expiry observed in #21); corpus videos found to be BYTE-DUPLICATE entries (original sha256 857e3b9b..., verified both sides via Download Original + shasum) - one rendition (06d814db..., ffmpeg 8.1.1 pinned invocation) uploaded to both entries; post-upload Play served playback.mp4 (Network filename switch); refusal cycle observed both directions (append-only attestation events); portrait quick-look bounding verified at 93db8aa. Venue: local dev against the prod Supabase project. Backfill-script defect found + ledgered (false PAIRING on SKIP; placeholder HASH passes guard; v2 candidate). Ledger lines: same-footage-different-bytes dupes evade the hash detector; HDR-to-8-bit tone-mapping = recipe-v2 candidate. Memos: `..._DW1A6_PLAYBACK_RENDITION_RULING.md` + `..._DW1A6_PLAYBACK_RENDITION_BUILD.md` (frontend _observations/). Gate semantics byte-for-byte unchanged; originals never modified; renditions regenerable.
- D-W1-A voice-attestation class + gated video playback DISCHARGED 2026-06-12: ruling memo of record frontend `b78070f` (mechanism-specification under spec 5.7, no amendment consumed); built PRs into #21, click-through fixes `da3ef95`, merged frontend main `cb3ba97`. Migration 015 `media_voice_attestations` live; G20 active; gov 116/0. OBSERVED in click-through: gate-pass mint, gate-fail neutral refusal, supersession gates forward, no autoplay, TTL 600s on-token, expired-URL rejection verbatim, full 69 MB original via fresh URL. Decode+seek blocked by HEVC in Chrome -> D-W1-A6 (Deferred). Memos: `..._DW1A_VOICE_ATTESTATION_RULING.md` + `..._DW1A_VOICE_PLAYBACK_BUILD.md` (frontend _observations/).
- Media EXPUNGEMENT ADMITTED + DISCHARGED (D-W1-E1 = Spec 5.2 Amendment 1, ratified 2026-06-11; ruling memo frontend `ff1b74b`): append-only expungement event is the RULED byte-deletion exception - tombstone + permanent when/who/why log, reason required, terminal (no reinstatement). Built PR #19 `7119651`; migration 014 live; G19 active. `..._MEDIA_EXPUNGEMENT_CANDIDATE.md` (flipped).
- W.1 (A/V Room) four-memo chain RATIFIED + FILED 2026-06-10 (SAT #1 native; D-W1-1..6 as recommended;
  governed-testimony fact class formalized per W.6 1.1, frame D1-D6 OPEN; W.6 7.2 on the contract card).
  E1.7 DISCHARGED-NATIVE (cross-surface SAT promotion pending). Inc 1 BUILD DISCHARGED: frontend
  `c21e858`->`df79a4f`->`c284053`->`7eee29d`->`65da2e6` (PR #2), click-through proven;
  `..._AV_ROOM_INCREMENT_1_CLICKTHROUGH.md`. Video HARDENING D1/D2/D3 `7601f8c`/`b97b19c`/`99dafc0`
  (PR #6 `2367479`) - superseded by the remedy-B 1 GB build.
- W.1 large-file ingest (**D-W1-V1 = remedy B**, Spec 5.1 Amendment 1) + ingest ergonomics (D0-D6)
  DISCHARGED 2026-06-11: client-direct upload under server-minted grant; cap 1 GB Pro; migration 012
  applied (G17 live, gov 113/0); posters confirmed on prod; >4.5 MB photo PROVEN TRANSITIVELY (68.7 MB
  carried the grant). Frontend `5c1550b` (remedy B, PR #10) + `c82bd5f` (ergonomics, PR #11);
  `..._DW1V1_RULING_REMEDY_B.md` / `..._REMEDY_B_LARGE_FILE_INGEST.md` / `..._INGEST_ERGONOMICS.md`.
- W.6 consent (2026-06-10): memo RATIFIED (D-S..D-X) + filed; `member_consent_events` (D-V) built +
  MERGED frontend `6c2ed32` (migration 010 append-only/member-only RLS, derived view, write API,
  panel `/league/[id]/consent`; G11 + click-through). Memos `..._W6_RATIFICATION`/`_AFFIRMATION`.
- W.7 framing drift-flag memo (cert-5 exhibit, doc-only): three 2026-06-09 engagement framings
  caught+reframed pre-build. `OBSERVATIONS_2026_06_10_W7_FRAMING_DRIFT_FLAG.md`.
- Residual fabrication remediation (verbatim guardrails): -51%; SERIES fixed, SUPERLATIVE up, FAAB unmoved (Deferred). `..._RESIDUAL_REMEDIATION_VERBATIM_RESULTS.md`.
- E1.4 fresh-gen fabrication baseline (gen `28d059f`): YELLOW - scores ~0.6%, non-score residual the headline. `..._E1_4_FRESH_GEN_FABRICATION_BASELINE_RESULTS.md`.
- `abd5c3c` historical weekly-windowing fix (D-W1=B; 2024-25 byte-identical; unblocked E1.4).
- `84284fe` E1.5b formatting gate (closes R5; L2 facts-block byte-identity HARD); E1.5a `b075b8a`.
- Charter v1.1 (2026-06-10, founder-instructed): section 4 records the per-repo ledger realization
  - engine `docs/STATE.md` (this file), frontend `ROADMAP.md` at root. Engine `11bdd8e` (PR #2);
  mirrored + v1.0.1-reconciled + charter-first-tracked frontend `3006834` (PR #4).
- `58b498a` E1.3 (DoR in-repo + charter v1.0.1) / `87c400f` E1.2 (ruff pre-commit gate) /
  `bf0833e` E1.1 (ruff cleanup + pin). Pre-charter: `a5d27dd` A2 anchor rename (Cavallini
  revocation `e5fbb94`/`97498fa`); `c4b4436` seasons-count; `993e97f` E2-light; `2bb33d0` docket.

## Known hazards

- Browser PR merge-clicks silently failed 3x (2026-06-11): button reported merged, remote unchanged. Merges are now performed by Claude Code via `gh pr merge` after CI verification; founder clicks remain for click-throughs only.
- Stale-brief hazard (7+ recurrences): brief claims without hashes are UNVERIFIED; if a brief
  conflicts with git, git wins - flag first. Corollary (2026-06-09): "data correct on prod is
  not the same as the code path guarded in the repo" - verify at the layer the claim is about.
- Local repos: engine = `~/projects/squadvault-ingest-fresh`; frontend = `~/squadvault`. BOTH
  prompt `squadvault %` - confirm before any write (`test -f scripts/recap_artifact_regenerate.py`
  TRUE in engine, FALSE in frontend). Deleted 2026-06-10: stale `~/projects/squadvault` engine
  clone + a `~/projects/squadvault-frontend` duplicate (both on origin).
- ruff: CI installs it UNPINNED (`.github/workflows/ci.yml` L29); the requirements pin (E1.1)
  only holds because L28 installs first. A future ruff release could surface lint without a bump.
- `prove_ci` needs Python 3.11+ (`prompt_audit_v1.py` uses `from datetime import UTC`); default
  `python3` is 3.10.4 (CI uses 3.12). `pyproject.toml` floor declares `>=3.11`.
- UP042 (str+Enum -> StrEnum) IGNORED in `pyproject.toml`, not fixed: 21 contract-bearing enums
  where StrEnum changes `str()`/format. DEFERRED - migrate in a dedicated unit, then drop ignore.
