# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter v1.0 section 4. Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- E1.4 fresh-gen fabrication baseline RUN + discharged as a measurement (gen HEAD
  `28d059f`, ~$0.60 est spend). Verdict YELLOW: scores clean (~0.6%), non-score residual
  is the headline (FAAB ~8.9%, series 3.8%, superlative 2.5%); remediation queue named,
  Phase 12 gating noted. Results: `OBSERVATIONS_2026_06_09_E1_4_..._BASELINE_RESULTS.md`.
  Enabled by the windowing fix (`abd5c3c`).

## Open units (Document of Record v2.1, by ID)

- E-cluster: E1.6, E1.7
- W-cluster: W.1, W.2, W.3, W.4, W.5, W.6, W.7, W.8
- L-cluster: L.1, L.2, L.3, L.4, L.5, L.6, L.7, L.8, L.9, L.10

(Descriptions now in-repo: `docs/SquadVault_Product_Document_of_Record_v2_1.md`.)

## Deferred (do not pick up until trigger)

  (E1.4 run + discharged as a measurement - see Discharged items and the results memo.)
- E1.6 (`promote-version` lifecycle): D-C adjudicated DEFER (2026-06-09). Optional;
  no DoR brief. Trigger: live season (E2.2) surfacing a real commissioner need to pick
  among regenerations. Type A scaffolding exists (`version_presentation_navigation_v1.py`);
  the action/UI layer is deliberately unbuilt until evidence defines it.
- E1.7 (Surface Admission Test first exercise): condition-gated; satisfied naturally by
  W.1/W.5 four-memo chains. Do not manufacture a candidate.

## Discharged items (with hashes)

- E1.4 fresh-gen fabrication baseline (gen HEAD `28d059f`): 32 weeks generated (~$0.60),
  verifier + automated classification. Verdict YELLOW (not a pass) - scores clean ~0.6%,
  non-score residual the headline (FAAB hottest); remediation queue named. Disclosed
  deviations: windowing fix post-dates prereg freeze; paced retry on rate-limited weeks.
  Results memo `OBSERVATIONS_2026_06_09_E1_4_FRESH_GEN_FABRICATION_BASELINE_RESULTS.md`.
- `abd5c3c` - Historical weekly-windowing fix (D-W1=B): week-field matchup selection for
  seasons with un-timestamped matchups; per-season gated so 2024-2025 stay byte-identical
  (0/288 working slots changed; 230 historical slots gained matchups; all 32 E1.4 weeks
  select matchups). New engine unit (not DoR); unblocks E1.4.
- `84284fe` - E1.5b: narrative formatting gate closes R5. Standalone presentation lint
  (L1-L5; L2 facts-block byte-identity is the one HARD rule) at the publication path +
  Office checklist; clean plain_text assembler lifted to render/. E1.5a spec at `b075b8a`.
- `58b498a` - E1.3: Document of Record filed in-repo + Map-registered; charter v1.0.1
  pointer amendment. Runbook DB-path item was already fixed at `215cb39` (no-op; the
  Document of Record listed it stale). Frontend doc sweep deferred to its own brief.
- `87c400f` - E1.2: pre-commit gate hardening - ruff added to the pre-commit chain
  + prove_ci, registry parity threaded (Labels TSV / Index / fingerprint / README),
  gate-wiring test. Closes Roadmap section 7.3 standing item.
- `bf0833e` - E1.1: ruff clean across generate_rivalry_chronicle_v1.py,
  rivalry_chronicle_generate_v1.py, editorial_review_week.py; E402s granted a
  per-file-ignore (legitimate load_dotenv-before-import); ruff pinned to 0.15.10.
- `a5d27dd` - A2 anchor test rename verified closed.
  (Brief labeled this "Cavallini rename"; the Cavallini/Mahomes anchor revocation
  itself is `e5fbb94` memo + `97498fa` purge. Flagged to founder - hash valid, label loose.)
- `c4b4436` - Phase 11 Roadmap seasons-count revision memo.
- `993e97f` - Phase 11 E2-light: initial archive generation (2 seasons, 35 weeks).
- `2bb33d0` - chronicle docket grammar: synthetic week_index dropped from
  multi-season dockets (closed by observation memo at `a9bc451`).

## Known hazards

- Stale-brief hazard (7+ recurrences): brief claims without commit hashes are
  UNVERIFIED. If a brief conflicts with git, git wins; flag before executing.
- "Data correct on prod is not the same as the code path being guarded in the repo"
  (2026-06-09): verify a claim at the layer the claim is about.
- CI installs `ruff` unpinned in `.github/workflows/ci.yml` line 29; the
  `requirements.txt` pin (E1.1) only sticks because line 28 installs it first.
  A future ruff release could surface new lint without a requirements bump.
- Local `prove_ci` needs Python 3.11+ but default `/usr/local/bin/python3` is
  3.10.4: `prompt_audit_v1.py` uses `from datetime import UTC` (3.11+). Run prove_ci
  under a 3.11+ `python3` (CI uses 3.12). The `pyproject.toml` floor now declares
  the true requirement (`requires-python = ">=3.11"`).
- UP042 (str+Enum -> StrEnum) is ignored in `pyproject.toml`, not fixed: 21 contract-
  bearing enums where StrEnum changes `str()`/format output. DEFERRED open item - migrate
  in a dedicated unit with determinism + golden-path validation, then drop the ignore.
