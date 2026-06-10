# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter v1.0 section 4. Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- W.6 consent gate CLOSED-THROUGH-BUILD: memo ratified 2026-06-10 (canonical
  `docs/SquadVault_W6_Consent_Governance_Memo_v1_2.md`; DoR v2.1.1 supersession note) and its
  `member_consent_events` system of record built + merged to frontend `main` (`6c2ed32`,
  founder-verified). W.1 (A/V Room) + L.3 (Vault, pre-Aug) consent predecessor satisfied.

## Open units (Document of Record v2.1, by ID; descriptions in-repo in the DoR)

- E-cluster: E1.6, E1.7. W-cluster: W.1, W.2, W.3, W.4, W.5, W.8 (W.6 discharged).
  L-cluster: L.1-L.10.
- W.6 follow-ups (frontend `~/squadvault`), minor/OPEN: (1) `founding_sessions.consent`
  reinterpretation doc-note (7.1); (2) commissioner read-only "at the gates" - DEFERRED to its
  first consumer (W.1/W.4/W.8); (3) auth-session governance tests (member-vs-member, no-proxy).
  Member-identity onboarding (E2.3) gates the ten members' use (commissioner works now).
  Binding (7.2): future chains declare categories-read / gate / revocation.

## Deferred (do not pick up until trigger)

- FAAB residual gate: FAAB fabrication instruction-resistant; trigger = a deterministic
  post-gen gate stripping any FAAB figure not on the canonical per-player allowlist.
- E1.6 (`promote-version`): D-C DEFER. Trigger: live-season (E2.2) need to pick among
  regenerations. Type A scaffold `version_presentation_navigation_v1.py` exists; UI unbuilt.
- E1.7 (SAT first exercise): condition-gated; satisfied by W.1/W.5 chains. Don't manufacture.

## Discharged items (with hashes)

- W.6 consent (Track W, 2026-06-10): memo RATIFIED (D-S..D-X as recommended) + filed canonical;
  `member_consent_events` (D-V) built + MERGED to frontend `main` `6c2ed32` (migration 010
  append-only / member-only RLS, derived view, write API, panel `/league/[id]/consent`; G11 +
  click-through verified). Memos `..._W6_RATIFICATION`(+`_AFFIRMATION`),
  `..._MEMBER_CONSENT_EVENTS_INCREMENT_1/2`.
- W.7 framing drift-flag memo (cert-5 exhibit, doc-only): three 2026-06-09 engagement framings
  caught+reframed pre-build. `OBSERVATIONS_2026_06_10_W7_FRAMING_DRIFT_FLAG.md`.
- Residual fabrication remediation (verbatim/copy guardrails): -51% residual; SERIES fixed,
  SUPERLATIVE improved, FAAB unmoved (see Deferred). `..._RESIDUAL_REMEDIATION_VERBATIM_RESULTS.md`.
- E1.4 fresh-gen fabrication baseline (gen `28d059f`): YELLOW - scores clean ~0.6%, non-score
  residual the headline. `..._E1_4_FRESH_GEN_FABRICATION_BASELINE_RESULTS.md`.
- `abd5c3c` historical weekly-windowing fix (D-W1=B; 2024-25 byte-identical; unblocked E1.4).
- `84284fe` E1.5b formatting gate (closes R5; L2 facts-block byte-identity HARD); E1.5a `b075b8a`.
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
