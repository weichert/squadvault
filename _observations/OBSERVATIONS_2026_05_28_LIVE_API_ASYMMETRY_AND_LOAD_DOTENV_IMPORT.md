# OBSERVATIONS — Live-API Asymmetry in Determinism Wrapper, and load_dotenv at Import Time (2026-05-28)

**Surfaced by:** Anomaly in the prove_ci run on commit `7602504` (carry-over cleanup session). Golden-path pytest Run B (non-repo CWD) reported `2308 passed, 3 skipped` against Run A's `2309 passed, 2 skipped`, with Run B completing in 71s vs Run A's 480s (6.7x speedup). All prior prove_ci runs in the same session showed identical pytest counts across Run A and Run B.
**Engine HEAD at observation:** `7602504`.
**Disposition:** Observation only. Root cause is transient (API account balance) and a latent pattern (load_dotenv at import time) that has worked reliably in production. No code change required today. A future refactor of the dotenv loading is a possible follow-up but not urgent.
**Append-only:** This memo records the finding. It does not edit any prior memo, gate, proof, or production code.

---

## The proof passed

The determinism proof's output-byte invariant held: `hash_a == hash_b == 8f9d384c...` across Run A (repo-root CWD) and Run B (non-repo CWD). The export artifacts are byte-identical regardless of caller CWD. This is the user-facing guarantee and it is sound.

The asymmetry below is in the test-count surface, which the proof does not assert on. Documenting why this is the right scope for the proof is part of this memo.

## The asymmetric skip

The single test that passed in Run A and skipped in Run B is `Tests/test_creative_layer_rivalry_v1.py::TestLiveAPI::test_live_narrative_draft`. It is the only test in the entire tracked suite that contains a runtime `pytest.skip(...)` call (line 208), which fires when the live Anthropic API returns None:

```python
if result is None:
    pytest.skip("API call returned None (likely invalid key or network issue) ...")
```

The test is also guarded by a collection-time `@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY", "").strip(), ...)` at line 189, which would normally cause the test to skip statically (in both Run A and Run B) when no API key is set. The session shell at observation time reported `ANTHROPIC_API_KEY: UNSET`. Yet the test clearly ran in Run A — otherwise it could not have appeared as PASSED.

## The shell-vs-runtime env divergence

The reason: `src/squadvault/core/queries/_run_event_queries.py`, `_run_franchise_snapshot.py`, and `_run_narrative_event_counts.py` each call `load_dotenv(".env")` at module-import time. The repo's `.env` file at the working tree root contains `ANTHROPIC_API_KEY`. When pytest imports anything that transitively pulls in those modules, `load_dotenv` populates `os.environ` inside the Python process. The shell env remains untouched, but the in-process env now has the key.

Diagnostic implication: `echo $ANTHROPIC_API_KEY` from the shell is NOT a reliable check for whether a Python process started in that shell will see the key. Tests, scripts, and proofs that import the queries layer will see the in-process env, not the shell env. This is a real divergence and easy to miss.

This is not a bug — `load_dotenv` is a common pattern. But it is a non-obvious behavior with diagnostic consequences.

## The account-balance proximate cause

The user added funds to the Anthropic API account immediately after the anomaly was surfaced, stating "my API account went negative." The proximate cause is:

- Run A executed with a barely-positive account balance. The API call succeeded. Test passed.
- The intervening 8 minutes of proof work (rivalry chronicle end-to-end, creative sharepack determinism, etc.) consumed enough API quota to push the account negative.
- Run B's call returned None (or raised an error swallowed by the production code's silent-fallback path). Runtime `pytest.skip` fired.

With funds added, subsequent prove_ci runs are expected to produce symmetric Run A and Run B counts (2309/2 in both), matching the immediately-prior session commits.

## The 6.7x speedup

Many tests in the suite exercise creative-layer codepaths via the production code's silent-fallback contract: when `ANTHROPIC_API_KEY` is set BUT the API call returns None/errors, the production code falls back to facts-only output without an exception. This is by design and well-tested.

In Run A, with the account positive, those codepaths got real API responses (slow). In Run B, with the account negative, the same codepaths took the silent fact-only fallback (fast). Many tests therefore ran in a fraction of the wall-clock time despite collecting and running the same test set. The 6.7x speedup is consistent with a large fraction of tests touching the creative layer.

This is not "Run B's working DB is warmed by Run A" (an earlier hypothesis). The working DB IS shared between Run A and Run B (`prove_ci.sh` sets `working_db` once per prove_ci invocation, and `prove_creative_determinism_v1.sh`'s `clean_outputs()` only deletes inside `artifacts/`, `out/`, and similar — not the temp working DB at `/tmp/squadvault_ci_workdb.*`). But the shared DB is not the dominant cause of the speedup; the API-fallback path is.

## Why the determinism proof is correctly scoped

The proof's invariant is: given identical inputs (fixture DB, repo state, code), the exported assembly bytes are identical regardless of caller CWD. Both Run A and Run B converge on the same final state of those assemblies because the production code is deterministic with respect to its inputs, AND the silent-fallback path produces byte-identical output to a successful API call from the export layer's perspective (the export rolls up facts; it does not embed creative prose into the determinism-checked artifact).

The proof does not assert on test count, test wall-clock time, or which fixtures executed. Those are not deliverable properties. Adding such assertions would tighten the proof at the cost of fragility against legitimate test-count drift (a new test added, a flake-prone integration test correctly skipping under low-network conditions, etc.).

## Latent architectural curiosity: load_dotenv at import time

Three production modules under `src/squadvault/core/queries/` call `load_dotenv(".env")` at module-import time. Two notes:

1. **The path is CWD-relative.** `load_dotenv(".env")` resolves relative to the Python process's current working directory at the time `load_dotenv` is called, NOT relative to the module's location. In the repo this is consistent because callers all run from REPO_ROOT, but a future deployment context that imports these modules from a different CWD would silently fail to load the intended file. A stray `.env` in some other CWD would silently load instead.

2. **Import-time side effects.** Module import has a side effect on `os.environ`. This is benign in practice but means that introspecting "what is the env" gives different answers before and after importing certain modules. Reproducible, but a footgun for diagnostics.

A future refactor could:
- Move dotenv loading to a single explicit bootstrap point (e.g., `squadvault.core.config.bootstrap_env()` called from CLI entrypoints, never from library-import paths)
- Use an absolute path derived from the module's `__file__` location, not CWD
- Skip dotenv loading entirely in test contexts (let conftest.py manage env explicitly)

This is a sizable refactor and not urgent. The pattern has worked reliably. Filing here so the future refactor proposal has a place to land.

## Provenance

The anomaly was discovered in the post-carry-over-cleanup prove_ci run on commit `7602504`. Investigation traced through:
1. Identified the only test with runtime `pytest.skip()`: `test_live_narrative_draft`
2. Confirmed shell env had `ANTHROPIC_API_KEY: UNSET`
3. Found `load_dotenv(".env")` calls in three query modules, explaining the shell-vs-runtime divergence
4. User confirmed account had gone negative during the prove_ci run, with funds since added

No code change. This memo and the next prove_ci run (expected symmetric A/B counts) close the investigation.
