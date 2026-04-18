# S10 Scope Correction: `raw_mfl_json` Inventory Across `core/` — 2026-04-18

**Companion to:** `_observations/ARCHITECTURAL_AUDIT_2026_04_16.md` (Surprise S10)
**Status:** Correction of an earlier claim in the audit. Written at the same time as the commit resolving the query-layer aspect of S10.
**Purpose:** Record, honestly, that the audit's S10 claim was overbroad; provide the full inventory S10's "quick grep" missed; and delimit what this session's fix does and does not do.

---

## The audit's claim

From `ARCHITECTURAL_AUDIT_2026_04_16.md`, Section 9:

> **S10.** `franchise_queries.py` is the only `core/` file that contains the substring `raw_mfl_json`
>
> Quick grep confirms. Core is otherwise free of MFL-specific payload-field references. This is the lone leak.

This is incorrect. The grep that produced the claim was partial. A full grep across `src/squadvault/core/` returns five files containing the substring, not one.

## Actual inventory

```
src/squadvault/core/queries/franchise_queries.py       (S10 target)
src/squadvault/core/canonicalize/run_canonicalize.py   (legitimate)
src/squadvault/core/recaps/facts/extract_recap_facts_v1.py
src/squadvault/core/recaps/context/player_narrative_angles_v1.py
src/squadvault/core/recaps/render/deterministic_bullets_v1.py
```

Classification of each:

| File | Classification | Rationale |
|---|---|---|
| `core/queries/franchise_queries.py` | **Layer leak** | Query helpers should read canonical fields; re-parsing adapter payloads for structured data violates the seam. This is the file S10 named and the one this session resolves. |
| `core/canonicalize/run_canonicalize.py` | **Legitimate** | Canonicalization is, definitionally, raw-to-canonical derivation. Reading `raw_mfl_json` is the module's job. A rule that forbade this would contradict the module's purpose. |
| `core/recaps/facts/extract_recap_facts_v1.py` | **Likely layer leak, larger scope** | `_parse_raw_mfl_json` helper used during fact extraction. Symptom is the same as S10: the canonical payload does not expose what the consumer needs, so the consumer re-parses. Resolution path is the same (promote fields at ingest), but the specific fields to promote are category-by-category and this is a larger surgery than franchise IDs. |
| `core/recaps/context/player_narrative_angles_v1.py` | **Likely layer leak, larger scope** | Trade loader reads player IDs from inside `raw_mfl_json` (explicit test coverage: `test_loads_trades_from_raw_mfl_json`). Would be resolved by promoting trade-player structure into the canonical trade payload at ingest. |
| `core/recaps/render/deterministic_bullets_v1.py` | **Likely layer leak, larger scope** | Trade-bullet renderer extracts franchise+player structure from `raw_mfl_json`. Same shape of fix as the other two consumer cases. |

## What this session's fix does

- Promotes `franchise_ids_involved: list[str]` into the canonical transaction payload at ingest (`src/squadvault/ingest/transactions.py`).
- Rewrites `core/queries/franchise_queries._franchise_ids_from_payload` to read only canonical fields (`franchise_ids_involved` preferred, scalar `franchise_id` as fallback for older events). Removes the `raw_mfl_json` parse path and its `json` import.
- Adds a gate test scoped to `core/queries/` (not all of `core/`) asserting no file under that subtree references `raw_mfl_json`.
- Adds behavior tests covering both the new canonical path and backward-compat for events predating the promotion.

## What this session's fix does not do

- Does not touch the three consumer-layer files classified above as "likely layer leak, larger scope." Each needs its own resolution pass with category-specific field promotion at ingest, and bundling them into this PR would violate the session's stopping discipline.
- Does not perform a backfill of historical memory events. The memory ledger is append-only; events ingested before `franchise_ids_involved` was promoted retain their old shape, and trade events among those will resolve to only their scalar initiator when queried through `_franchise_ids_from_payload`. This under-representation is documented in the helper's docstring. A backfill is a separate, explicit decision.
- Does not add a global `core/`-wide grep gate. Such a gate would fail on day one because of the legitimate `canonicalize` reference, and the remaining consumer-side touches are not addressed in this PR.

## Why this correction is recorded at commit time

Two reasons. First, the audit stands in the repo; leaving its S10 overclaim unanswered alongside a fix that partially contradicts it is worse than either producing this correction or never having made the claim. Second, this document is where the three remaining consumer-layer leaks are named, so that a future session picking up the broader cleanup knows exactly which files are on the table and why.

## Lineage

- Audit claim introduced: `ARCHITECTURAL_AUDIT_2026_04_16.md`, Section 9, S10.
- Scope read that surfaced the correction: tonight, against HEAD `d7c403b`.
- Resolution commit: the same commit this observation is included in.

---

## 2026-04-18 update: trade-loader leak closed

The second "likely layer leak, larger scope" row in the inventory table — `core/recaps/context/player_narrative_angles_v1.py`, trade loader — has been resolved. The fix follows the same ingest-promotion / consumer-canonical-read pattern as the query-layer fix in commit `6eab1e0`, with one deliberate deviation.

**Ingest-side promotion.** `derive_transaction_event_envelopes` now calls a new `_parse_trade_gave_up` helper that reads `franchise1_gave_up` / `franchise2_gave_up` from the raw MFL trade dict and promotes them into the canonical payload as `trade_franchise_a_gave_up` and `trade_franchise_b_gave_up`. Non-trade transactions receive these fields as empty lists so the envelope shape stays stable across transaction types — the same shape discipline `franchise_ids_involved` already follows.

**Consumer-side canonical-first read.** `_load_season_trades` now delegates to a new `_resolve_trade_structure` helper which reads canonical fields first (trigger: `len(franchise_ids_involved) >= 2` AND either `trade_franchise_a_gave_up` or `trade_franchise_b_gave_up` key is present in the payload) and falls back to parsing `raw_mfl_json` when those conditions fail. A new test (`test_canonical_path_wins_over_raw_mfl_json_mismatch`) poisons `raw_mfl_json` with deliberately wrong values and asserts the canonical values surface — a regression guard against the consumer ever silently drifting back to raw-first reading.

**Deliberate deviation from the query-layer fix.** The query-layer S10 fix (6eab1e0) accepted silent under-representation for pre-promotion events. For trades we kept the `raw_mfl_json` fallback instead, because silent under-representation on historical trade events would produce an immediately visible regression in TRADE_OUTCOME angle firing across every past season. The fallback is documented as the residual S10 touchpoint in `core/recaps/context/` pending an explicit historical-backfill decision. This decision deferral is recorded here rather than taken unilaterally.

**Gate-test shape not yet achievable.** Because the consumer still references `raw_mfl_json` via the fallback path, a `test_*_layer_boundary` guard analogous to `Tests/test_core_queries_layer_boundary_v1.py` cannot be added to `core/recaps/context/` yet. Retiring the fallback — and with it, adding the gate — is bundled into the future backfill decision.

**Remaining inventory.** Two "likely layer leak, larger scope" files remain untouched: `core/recaps/facts/extract_recap_facts_v1.py` and `core/recaps/render/deterministic_bullets_v1.py`. The inventory table above is unchanged so that the April 18 baseline it describes stays readable in its own right.

---

*End of document.*
