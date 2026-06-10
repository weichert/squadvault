# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter v1.0 section 4. Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- W.6 chain prep: detailed Fable brief filed (`c441c75`) and the resulting v1.2 DRAFT's
  Section 0 substrate finding INDEPENDENTLY VERIFIED at frontend `4e44bb3` (all 8 Appendix A
  claims confirmed; one non-load-bearing A8 table-count imprecision noted). W.6 itself is a
  chat/Fable constitutional artifact, NOT yet in-repo and NOT yet ratified - awaiting founder
  ratification + D-S..D-X picks. Prior HEAD: W.7 framing drift-flag memo (Track W entered).

## Open units (Document of Record v2.1, by ID)

- E-cluster: E1.6, E1.7
- W-cluster: W.1, W.2, W.3, W.4, W.5, W.6, W.8
- L-cluster: L.1, L.2, L.3, L.4, L.5, L.6, L.7, L.8, L.9, L.10

(Descriptions now in-repo: `docs/SquadVault_Product_Document_of_Record_v2_1.md`.)

## Deferred (do not pick up until trigger)

- FAAB residual gate (NEW, from remediation): FAAB fabrication is instruction-resistant
  (copy-only did not move it). Trigger: build a deterministic post-generation gate that
  strips/blocks any FAAB dollar figure not on the canonical per-player allowlist.
- E1.6 (`promote-version` lifecycle): D-C adjudicated DEFER (2026-06-09). Optional;
  no DoR brief. Trigger: live season (E2.2) surfacing a real commissioner need to pick
  among regenerations. Type A scaffolding exists (`version_presentation_navigation_v1.py`);
  the action/UI layer is deliberately unbuilt until evidence defines it.
- E1.7 (Surface Admission Test first exercise): condition-gated; satisfied naturally by
  W.1/W.5 four-memo chains. Do not manufacture a candidate.

## Discharged items (with hashes)

- W.7 (framing drift-flag memo, FIRST on Track W): records the three 2026-06-09 vision-session
  engagement framings, each caught+reframed before any build (worthy-of-visits / corkboard /
  words-become-facts-behavior-never-measured). cert-5 primary exhibit. Doc-only, no tier.
  Memo `OBSERVATIONS_2026_06_10_W7_FRAMING_DRIFT_FLAG.md`.
- Residual fabrication remediation (verbatim/copy guardrails for superlative/series/FAAB):
  -51% residual fabrication; SERIES fixed, SUPERLATIVE improved, FAAB unmoved (see Deferred).
  Memo `OBSERVATIONS_2026_06_09_RESIDUAL_REMEDIATION_VERBATIM_RESULTS.md`.
- E1.4 fresh-gen fabrication baseline (gen HEAD `28d059f`, ~$0.60): YELLOW (not a pass) -
  scores clean ~0.6%, non-score residual the headline. Deviations: windowing fix post-dates
  prereg freeze; paced retry. Memo `..._E1_4_FRESH_GEN_FABRICATION_BASELINE_RESULTS.md`.
- `abd5c3c` - Historical weekly-windowing fix (D-W1=B): week-field matchup selection;
  per-season gated, 2024-2025 byte-identical; all 32 E1.4 weeks select matchups. Unblocks E1.4.
- `84284fe` - E1.5b: narrative formatting gate closes R5 (presentation lint L1-L5; L2
  facts-block byte-identity HARD). E1.5a spec at `b075b8a`.
- `58b498a` E1.3 (Document of Record in-repo + charter v1.0.1; runbook already fixed
  `215cb39`) / `87c400f` E1.2 (ruff pre-commit gate + registry parity) / `bf0833e` E1.1
  (ruff cleanup + pin 0.15.10). See per-unit memos.
- Pre-charter: `a5d27dd` A2 anchor rename (Cavallini revocation `e5fbb94`/`97498fa`);
  `c4b4436` seasons-count memo; `993e97f` E2-light archive; `2bb33d0` docket grammar.

## Known hazards

- Stale-brief hazard (7+ recurrences): brief claims without commit hashes are
  UNVERIFIED. If a brief conflicts with git, git wins; flag before executing.
- Divergent clones: `~/projects/squadvault` is a stale ENGINE clone (`a5a2d60`) separate
  from the working repo (`squadvault-ingest-fresh`); `~/projects/squadvault-frontend` is the
  frontend clone (left detached at `4e44bb3` after W.6 verification). Confirm repo identity
  before acting (`test -f scripts/recap_artifact_regenerate.py` = engine working repo).
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
