# STATE.md - SquadVault Engine State Ledger

Read-model summary per Charter v1.0 section 4. Git is the read-model; this file is
a derived index, kept under ~80 lines. Updated in every session's commit series.
No session treats a prior chat message or brief as authoritative over `git log` + this file.

## Current HEAD

- `bf0833e` - E1.1 discharged: ruff errors cleared across chronicle/consumer modules;
  ruff pinned to 0.15.10. Preceded by charter adoption (`d119e6e`) and STATE.md ledger.

## Open units (Document of Record v2.1, by ID)

- E-cluster: E1.2, E1.3, E1.4, E1.5, E1.6, E1.7
- W-cluster: W.1, W.2, W.3, W.4, W.5, W.6, W.7, W.8
- L-cluster: L.1, L.2, L.3, L.4, L.5, L.6, L.7, L.8, L.9, L.10

(Descriptions live in the Document of Record / chat project knowledge, not duplicated here.)

## Discharged items (with hashes)

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
  under a 3.11+ `python3` (CI uses 3.12). Latent: `pyproject.toml` declares
  `requires-python = ">=3.10"` while the code actually requires 3.11+ (unscoped fix).
