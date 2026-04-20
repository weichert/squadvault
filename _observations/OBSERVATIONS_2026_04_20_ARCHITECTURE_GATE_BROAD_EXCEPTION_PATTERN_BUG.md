# Architecture gate broad-exception pattern-match bug

**Date:** 2026-04-20
**Scope:** Read-only observation. No `src/` or `Tests/` changes.
Documents a pre-existing defect in
`Tests/test_architecture_gates_v1.py::test_core_broad_exception_count`
surfaced incidentally during the 2026-04-20 retirement session for
`render_recap_text_from_facts_v1.py`, and corrects a load-bearing
recommendation in the dormancy memo that depended on the defect
not existing.
**HEAD at observation-time:** `ff63361` — Retire dormant renderer
render_recap_text_from_facts_v1.
**Follows:** `ff63361` retirement; `0b280cb` dormancy memo whose
gate-baseline recommendation is corrected by this memo.

---

## Headline finding

`Tests/test_architecture_gates_v1.py::test_core_broad_exception_count`
does not catch the broad-exception form used throughout the
codebase. Its match pattern is restricted to two exact strings:

```python
if line.strip() in ("except Exception:", "except Exception as e:"):
```

All non-bare handlers in `src/squadvault/core/` use the form
`except Exception as exc:` — a different variable name. The test's
`in` check is exact-string membership, not prefix or pattern
matching, so `as exc:` forms are missed entirely. The gate catches
1 of 7 actual handlers at HEAD `ff63361`.

The assertion baseline (`count <= 8`) and the inline breakdown
comment (2 canonicalize + 2 deterministic_bullets + 2
render_recap_text_from_facts = 6 with 2-slack buffer) are both
fiction. The "canonicalize" line has no basis in current source
(the cited behavior lives in `recap_verifier_v1.py`, not a
canonicalize module). The "2 in deterministic_bullets" and "2 in
render_recap_text_from_facts" entries describe handlers that exist
but that the test has never actually counted.

The defect is pre-existing and independent of any Phase 10 thread.
It was surfaced here because retiring the dormant renderer required
empirical verification of the baseline before editing it — and that
verification revealed the baseline was meaningless to begin with.

---

## Evidence

### Post-retirement handler population at HEAD `ff63361`

7 broad-exception handlers across 4 files:

```
src/squadvault/core/recaps/verification/recap_verifier_v1.py:2466:    except Exception:
src/squadvault/core/recaps/render/deterministic_bullets_v1.py:52:    except Exception as exc:
src/squadvault/core/recaps/render/deterministic_bullets_v1.py:63:    except Exception as exc:
src/squadvault/core/recaps/context/league_rules_context_v1.py:52:    except Exception as exc:
src/squadvault/core/recaps/context/bye_week_context_v1.py:59:    except Exception as exc:
src/squadvault/core/resolvers.py:124:        except Exception as exc:
src/squadvault/core/resolvers.py:213:        except Exception as exc:
```

6 of 7 use `except Exception as exc:`. Exactly one —
`recap_verifier_v1.py:2466` — uses the bare form `except
Exception:`. The test's `in` check catches only that one bare case.

Test-caught count is 1 of 7 at HEAD. Pre-retirement it was 1 of 9
(the two handlers removed by `ff63361` in
`render_recap_text_from_facts_v1.py:47, :264` both used `as exc:`
and were never caught by the test pattern either).

### Test source

`Tests/test_architecture_gates_v1.py:197-214`:

```python
def test_core_broad_exception_count(self):
    """Core modules should not accumulate broad except Exception handlers."""
    count = 0
    files = glob.glob(os.path.join(SRC, "squadvault", "core", "**", "*.py"), recursive=True)
    for f in files:
        if "__pycache__" in f:
            continue
        with open(f) as fh:
            for line in fh:
                if line.strip() in ("except Exception:", "except Exception as e:"):
                    count += 1
    # Baseline: 6 legitimate fail-safe guards in renderers/canonicalize.
    # 2 in canonicalize (ROLLBACK guard), 2 in deterministic_bullets (resolver fallback),
    # 2 in render_recap_text_from_facts (str fallback + bullet enrichment guard).
    assert count <= 8, (
        f"Core broad exception count grew to {count}. "
        f"Expected <=8. Narrow new handlers to specific exception types."
    )
```

The assertion `count <= 8` is trivially satisfied by `1 <= 8`
regardless of how many `as exc:` handlers accrue. The inline
breakdown is not derivable from the test's actual match logic; it
reads like documentation written against an intended pattern rather
than the implemented one.

### Origin hypothesis (not load-bearing)

The pattern likely dates to an earlier convention where handlers
used `as e:`. The codebase has since standardized on `as exc:`, but
the gate test's match pattern was not updated to track the
convention change. This is a hypothesis — the memo does not rely on
it being correct; whatever the provenance, the current behavior is
the current behavior.

---

## Classification

**Pre-existing defect, independent of Phase 10 thread.** Not caused
by the renderer retirement; not caused by any recent change visible
in the session's working set. The retirement's effect on the gate
is to reduce the actual handler population from 9 to 7, but since
the test catches 1 either way, no assertion dynamics change across
`ff63361`.

The defect has been silently inert for an unknown duration — the
gate provides no meaningful coverage today and has not for some
time. Until fixed, the invariant "broad exception handlers in core/
should not grow" is enforced only against the narrow case where
someone writes a bare `except Exception:` without a variable
binding.

---

## Corrections to prior memo `0b280cb`

The 2026-04-20 dormancy memo (commit `0b280cb`) recommended as part
of the retirement plan:

> Lower the `test_core_broad_exception_count` gate baseline from
> `<=8` to `<=6` and update the inline breakdown comment at
> `Tests/test_architecture_gates_v1.py:208-210`.

That recommendation was based on an uncritical reading of the
inline breakdown comment, not on empirical verification of the
test's actual match behavior. The recommendation as written would
have:

- Lowered the assertion to `<=6` — still trivially satisfied by
  `1 <= 6`, providing no additional coverage.
- Updated the inline comment to describe a 4-handler post-retirement
  baseline — equally fictional relative to what the test actually
  counts.

The retirement session on 2026-04-20 (resulting in commit
`ff63361`) declined that recommendation after empirical
verification (Option A) and deferred gate-test handling to this
memo.

The dormancy memo itself is not edited — memos are history and
corrections live adjacent, not inline.

---

## Recommended next-step session

Fix the gate test as its own single-topic commit in a dedicated
session. Three candidate fix shapes, in order of conservatism:

**(α) Regex expansion.** Replace the `in`-tuple check with a regex
match that catches `except Exception:` and `except Exception as
<any_name>:`. Minimum code change consistent with the test's
apparent intent. Post-fix empirical count becomes 7; set assertion
to `<=9` (preserving the 2-slack buffer pattern) or `<=7` (tight).
Comment rewritten with the actual 4-file breakdown.

**(β) AST-based check.** Parse each `.py` file with `ast`, walk for
`ExceptHandler` nodes whose `type` is `Name(id="Exception")`. More
robust against formatting variations (multi-line `except` clauses,
unusual spacing, parenthesized exception tuples containing
`Exception`). Heavier dependency surface for an architecture gate.

**(γ) Reframe as a "no bare-except-Exception" gate.** Keep the
string match for `except Exception:` only (drop the `as e:` branch),
drop the handler-count baseline entirely. Assertion becomes "no
bare `except Exception:` in core/." Add a separate lint rule
(ruff's `BLE001` or similar) to enforce variable binding on broad
catches. This reshapes the test's purpose rather than fixing its
original purpose.

**Lean: α.** Minimum-change, preserves the test's original intent
(count-based hygiene), and the fix is a small mechanical edit that
can be verified empirically in one commit. (β) is overbuilt for
the problem; (γ) is a scope change that should be its own design
decision, not a fix pass.

A single-topic fix-session commit under (α) would touch one file
(`Tests/test_architecture_gates_v1.py`), adjust three lines (the
match logic and the assertion), and rewrite the 3-line inline
comment. Commit body should reference this memo.

---

## Out of scope

- Any change to `Tests/test_architecture_gates_v1.py` — fix is a
  separate session.
- Any edit to `_observations/OBSERVATIONS_2026_04_20_RENDER_RECAP_TEXT_FROM_FACTS_V1_DORMANCY.md`.
  Memos are history; corrections live adjacent.
- Any broader audit of other architecture gate tests in
  `test_architecture_gates_v1.py` for analogous pattern-match bugs.
  Possible but unscoped; a future session could sweep the whole
  file's gate assertions for empirical-vs-documented drift.
- Any change to the handlers themselves (narrowing `except
  Exception as exc:` to specific exception types in the 6 non-bare
  sites). Orthogonal question, not part of the gate's intent.

---

## Cross-references

- **Commit `ff63361`** (2026-04-20) — "Retire dormant renderer
  render_recap_text_from_facts_v1." The retirement session that
  surfaced this finding. Commit body names the deferral.
- **Memo `0b280cb`** (2026-04-20) — "Phase 10 observation:
  render_recap_text_from_facts_v1.py dormancy pass." The memo
  whose gate-baseline recommendation is corrected here.
- **Session sequence** — Dormancy memo `0b280cb` → retirement
  `ff63361` → this memo. Three commits, three topics, one session.
