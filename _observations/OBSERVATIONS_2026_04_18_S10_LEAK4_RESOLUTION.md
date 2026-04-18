# S10 Leak #4 Resolution: `deterministic_bullets_v1.py` canonical-first — 2026-04-18

**Companion to:** `_observations/OBSERVATIONS_2026_04_18_S10_SCOPE_CORRECTION.md` (the inventory that named this file as one of three consumer-layer leaks)
**Status:** Resolution of the last consumer-layer leak listed in the scope correction.

---

## What this session's fix does

- Rewrites `core/recaps/render/deterministic_bullets_v1.py` to read the canonical trade structure (`trade_franchise_a_gave_up`, `trade_franchise_b_gave_up`, alongside already-promoted `franchise_id` and `franchise_ids_involved`) via a new helper `_extract_canonical_trade`. Franchise A is taken from `franchise_id` (the MFL initiator); Franchise B is derived as the first member of `franchise_ids_involved` that is not franchise A.
- Key-presence on `trade_franchise_a_gave_up` is the post-promotion signal. When the key is absent — events ingested before the S10 leak #2 resolution at `b26e93f` promoted these fields — the renderer falls back to `_extract_mfl_trade` parsing `raw_mfl_json`. Same retention pattern as S10 leak #1.
- No ingest-side work in this commit: all fields this consumer needs were already promoted by leak #2. The `ad3cb98` `transactions.py` shape (`trade_franchise_a_gave_up` / `trade_franchise_b_gave_up` / `trade_comments` / `trade_expires_timestamp`, defaulted to empty-list/None on non-trades) was sufficient as-is.
- Four regression tests added in `TestTradeCanonicalPath`: canonical path with resolvers; canonical priority when both canonical and `raw_mfl_json` are present; one-sided gave-up lists producing "completed a trade"; fallback to `raw_mfl_json` when franchise B cannot be derived from `franchise_ids_involved`.

## What this session's fix does not do

- Does not remove `raw_mfl_json` from `deterministic_bullets_v1.py`. The fallback helper retains the reference with a narrowed docstring scoping it to pre-promotion events. This mirrors leak #1's retention of the scalar `franchise_id` fallback in `_franchise_ids_from_payload` and matches the invariant that the memory ledger is append-only (old events keep their old shape).
- Does not touch `waiver_bids.py` ingest. `WAIVER_BID_AWARDED` bullet rendering already consumes canonical `franchise_id` / `player_id` / `bid_amount` and does not reach into `raw_mfl_json`. The separate backlog item for `WAIVER_BID_*` ingest-time promotion stands.
- Does not add a `core/recaps/render/`-wide grep gate. Such a gate would fire on the intentional fallback helper; scoped enforcement would need to allowlist the fallback path explicitly and is deferred.

## Scope discovery (not addressed in this pass)

`src/squadvault/core/recaps/render/render_deterministic_facts_block_v1.py` reads `memory_events.payload_json` directly via `_fetch_memory_payloads_by_ids`. `src/squadvault/core/storage/sqlite_store.py` (lines 74–76) explicitly documents that "memory_events is an internal ledger and must not be consumed directly" and directs consumers to `v_canonical_best_events`. This is a latent seam issue, not a functional problem — `memory_events.payload_json` stores the ingest envelope verbatim, so the payload shape reaching the bullet renderer is the same either way. Flagged for a future pass; out of scope for leak #4.

## Lineage

- Scope correction that named this file: `_observations/OBSERVATIONS_2026_04_18_S10_SCOPE_CORRECTION.md`, committed alongside the query-layer resolution.
- Ingest-side prerequisite: S10 leak #2 resolution at `b26e93f` promoted `trade_franchise_a_gave_up` / `trade_franchise_b_gave_up` on `TRANSACTION_TRADE` envelopes.
- Consumer-side rewrite: this commit.

---

*End of document.*
