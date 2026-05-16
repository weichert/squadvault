# A2 Test Rename Standing Item -- Discharged
## SquadVault | Phase 11 | 2026-05-16

**Standing item:** Roadmap v2 section 7.3 -- "A2 anchor correction:
test_cavallini_mahomes_2018_qb_anchor_regression rename pending."

**Disposition:** Discharged. No rename needed.

---

## Finding

The test name `test_cavallini_mahomes_2018_qb_anchor_regression` does not
exist in the codebase. A grep across Tests/ for "cavallini_mahomes_2018"
returns zero hits.

The actual test in question is
`TestComputeAuctionMostExpensiveV1.test_qb_position_record_computed_independently_of_overall`
in Tests/test_draft_history_vault_aggregations_v1.py. That name is accurate
and requires no correction.

The anchor revocation (player 9988 is Antonio Brown, not Mahomes) was
already handled at A2 spec/test authoring time:

- The module docstring (lines 9-14) explicitly records the revocation
  and notes the derivation behavior is unaffected.
- The test docstring records the revocation inline with a pointer to
  the revocation memo.
- The synthetic test data uses player_id="qb_anchor" (not "9988"),
  deliberately decoupled from any real player identity.

The standing item was a stale carry-forward. The rename was anticipated
in the Roadmap v2 section 7.3 but had already been handled at the time
the tests were authored.

**No code change. Standing item closed.**

---

Filed: 2026-05-16
HEAD at filing: da9866b
