# A2 Anchor Test Rename - Verified Closed

Engine HEAD at verification: 353bb64
Date: 2026-06-08
Type: standing-item closure / doc-only memo. No fact writes; no code change.

## The standing item
Roadmap v2 (OBSERVATIONS_2026_05_16_PHASE_11_ROADMAP_V2.md) section 7.3 and the
A3 implementation memo (OBSERVATIONS_2026_05_16_A3_IMPLEMENTATION.md, lines
102-103) both list an open item: rename the test
test_cavallini_mahomes_2018_qb_anchor_regression, because the 2018 anchor was
revoked (player 9988 is Antonio Brown, a WR, not Patrick Mahomes), with a
"correction memo pending."

## Verification
At HEAD 353bb64 the item is already fully resolved; it was completed after the
2026-05-16 memos were authored.

- The function test_cavallini_mahomes_2018_qb_anchor_regression no longer exists
  anywhere in Tests/ (zero occurrences of that name across the tree).
- It was renamed to test_qb_position_record_computed_independently_of_overall
  in Tests/test_draft_history_vault_aggregations_v1.py.
- The correction went beyond the name: the module docstring and the test
  docstring both record that earlier versions referenced the "Cavallini/Mahomes
  2018 anchor," that it was revoked 2026-05-14 (player 9988 is Antonio Brown,
  not Mahomes), and they cite
  OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md.
- The test body was decoupled from any real pick: it uses synthetic data
  (player_id "qb_anchor", plus a higher-bid RB) as a pure test target for
  "QB-position record computed independently of overall." It no longer asserts
  anything about a real franchise or player.
- The revocation memo (OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md)
  exists and is the correction record, so the "correction memo pending" note is
  also satisfied.

## Disposition
No code change is owed. The test is correct, decoupled from the revoked anchor,
and self-documenting. Roadmap v2 section 7.3 still lists the item as open
because the Roadmap is append-only and is not silently patched (section 8.6);
the entry self-resolves at the next Roadmap revision or at the Phase 11 Closure
Memo. This memo records the verified-closed state so the item is not re-chased
in a future session.

The historical A2 specification and decision-readiness memos that still mention
the "Cavallini / Mahomes" example are append-only _observations records,
correctly superseded on the factual point by the 2026-05-14 revocation memo;
they are not patched.

## Provenance
Doc-only. No canonical_events / memory_events writes; no code change; no
narrative generation; no API; no approvals.
