# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter v1.0 section 4. Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- E1.3 discharged: Document of Record filed in-repo (`58b498a`) + charter v1.0.1 pointer
  amendment; runbook DB-path verified already fixed (`215cb39`). Preceded by E1.2 ruff
  pre-commit gate (`87c400f`) and the requires-python >=3.11 bump.

## Open units (Document of Record v2.1, by ID)

- E-cluster: E1.4, E1.5, E1.6, E1.7
- W-cluster: W.1, W.2, W.3, W.4, W.5, W.6, W.7, W.8
- L-cluster: L.1, L.2, L.3, L.4, L.5, L.6, L.7, L.8, L.9, L.10

(Descriptions now in-repo: `docs/SquadVault_Product_Document_of_Record_v2_1.md`.)

## Deferred (do not pick up until trigger)

- E1.4: gated on a Fable pre-registration protocol + D-B (n/spend cap); skeleton
  `session_brief_e1_4_execution_SKELETON.md`. Trigger: protocol memo filed.
- E1.5b: gated on the E1.5a presentation spec (Fable, pre-Week-1); skeleton
  `session_brief_e1_5b_formatting_gate_SKELETON.md`. Trigger: E1.5a spec in `docs/`.
- E1.6 (`promote-version` lifecycle): D-C adjudicated DEFER (2026-06-09). Optional;
  no DoR brief. Trigger: live season (E2.2) surfacing a real commissioner need to pick
  among regenerations. Type A scaffolding exists (`version_presentation_navigation_v1.py`);
  the action/UI layer is deliberately unbuilt until evidence defines it.
- E1.7 (Surface Admission Test first exercise): condition-gated; satisfied naturally by
  W.1/W.5 four-memo chains. Do not manufacture a candidate.

## Discharged items (with hashes)

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
