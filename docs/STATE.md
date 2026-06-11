# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter section 4 (amended v1.1, 2026-06-10). Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- W.1 (A/V Room) Increment 1 MERGED + PROVEN + DISCHARGED (frontend `65da2e6`, PR #2; foundation
  `2cd9f17`, PR #1, live on Supabase - tables+RLS, `league-media` private, storage policy; five
  `/api/av-room/*` routes + ingest/display; G12-15 assert RLS 42501; click-through proven end-to-end).
  Video-ingest hardening D1/D2/D3 MERGED (frontend PR #6 `2367479`, see Discharged) - poster shows;
  PLAYBACK still DEFERRED (attestation is its OWN class + 2b gate, NOT a soft tag; option-3 rejected
  2026-06-10). Chain RATIFIED+FILED 2026-06-10 (SAT #1; D-W1-1..6; 7.2 on card). Inc 2 (member) gated E2.3.

## Open units (Document of Record v2.1, by ID; descriptions in-repo in the DoR)

- E-cluster: E1.6 (E1.7 DISCHARGED-NATIVE via the W.1 chain). W-cluster: W.1 (Inc 1 DISCHARGED;
  open = video increment + Inc 2), W.2, W.3, W.4, W.5, W.8. L-cluster: L.1-L.10.
- W.1 open work (on the proven Inc 1 foundation): (a) VIDEO hardening D1/D2/D3 MERGED (Discharged);
  large-file ingest **D-W1-V1 RULED REMEDY B** + **Spec 5.1 Amendment 1** 2026-06-10 (client-direct
  under server-minted grant; A eliminated by Vercel's 4.5 MB body limit, cap now 1 GB Pro). Remedy-B
  build MERGED (frontend `5c1550b`, D-B1..D-B5, gov 112/0; photo >4.5 MB proven transitively, 68.7 MB
  on prod). INGEST ERGONOMICS D0-D6 (poster set+de-silence, drag-drop queue, batch-tag, compact rows,
  newest-first, reinstate=mig 012+G17, HEIC) BUILT in PR; founder: apply 012, set 2 stills,
  click-through. **D-W1-V1 DISCHARGE HELD on D0 (posters on prod).** PLAYBACK = Fable-spec-first.
  (b) Inc 2 (member captions/marginalia/self-tag) gated E2.3 - first live 2a-silence (no linked member_user_id; spec 8.1; commish id works).
  (c) Two ingest-extension candidates REGISTERED + PARKED (Google Photos Picker import; EXIF date-proposal, build gated on a recorded-metadata decision note) - trigger = first real shoebox session; `..._W1_INGEST_EXTENSION_CANDIDATES.md`.
- W.6 follow-ups: (1) 7.1 doc-note FILED (frontend `248895c`); (2) commissioner read-only "at
  the gates" DEFERRED to first consumer (W.1/W.4/W.8); (3) auth-session governance tests -
  follow-up. Binding (7.2): future chains declare categories-read / gate / revocation.

## Deferred (do not pick up until trigger)

- FAAB residual gate: FAAB fabrication instruction-resistant; trigger = a deterministic
  post-gen gate stripping any FAAB figure not on the canonical per-player allowlist.
- E1.6 (`promote-version`): D-C DEFER. Trigger: live-season (E2.2) need to pick among
  regenerations. Type A scaffold `version_presentation_navigation_v1.py` exists; UI unbuilt.

## Discharged items (with hashes)

- W.1 (A/V Room) four-memo chain RATIFIED + FILED 2026-06-10 (SAT #1 native admission;
  D-W1-1..6 as recommended). Governed-testimony fact class formalized (Manual Fact Import
  admissibility theory in analogue, per W.6 1.1; frame D1-D6 untouched/OPEN); W.6 7.2
  declaration on the contract card. E1.7 DISCHARGED-NATIVE (cross-surface SAT promotion still
  pending). W.1 Increment 1 BUILD DISCHARGED 2026-06-10: frontend `c21e858`->`df79a4f`->`c284053`
  ->`7eee29d`->`65da2e6` (PR #2), founder click-through proven; frontend ledger ROADMAP.md W.1 row
  + `..._AV_ROOM_INCREMENT_1_CLICKTHROUGH.md`; chain/contract/SAT-addendum memos filed 2026-06-10.
  Video-ingest HARDENING D1/D2/D3 `7601f8c`/`b97b19c`/`99dafc0`, PR #6 `2367479` (made the cap honest,
  not raised; `..._AV_ROOM_VIDEO_INGEST_HARDENING.md`) - superseded by the remedy-B 1 GB build.
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
