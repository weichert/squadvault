# Observation: Finding B closure — strip dormant checks from gate_prove_ci_structure_canonical_v1

**Session date:** 2026-04-27
**Origin:** Finding B from F3 retirement memo + Finding D apply-script
discovery. Sed `\b` portability bug + worktree_cleanliness intentional-
multi-invocation pattern.
**HEAD before:** `dc2b2bf` (Findings C+E followup)
**Decision:** Strip the gate to its banner-uniqueness check. Drop the
broken path-uniqueness and path-ordering checks.

---

## Summary

The structure_canonical gate had three checks. Two were broken in
opposite directions on macOS BSD vs Linux GNU sed; the third worked
correctly and provides real value.

This commit removes the two broken checks. The gate file stays in
place (no rename, no Index/TSV/fingerprint churn) but its content
narrows to just the banner-uniqueness check.

---

## Diagnosis

### Check 1 (path uniqueness) and Check 2 (path ordering) — both broken

Path extraction line:
```sed
sed -E 's/^.*\b(\.\/)?(scripts\/gate_[^[:space:]]+\.sh)\b.*$/\2/'
```

`\b` (word boundary) is GNU-sed only. macOS BSD sed treats `\b` as
literal — the regex `^.*\b...` becomes "match `^.*` followed by literal
backslash-b followed by `(...)` followed by literal backslash-b
followed by `.*$`" — which never matches, so sed passes the input
through unchanged.

Result:
- **macOS BSD sed:** `paths_file` contains full prove_ci.sh lines
  (with `bash`, with quoted args, with comments). Each line is unique.
  Uniqueness check passes (false-negative). Lines happen to be in some
  order; ordering check passes by chance or fails by chance — either
  way it's not testing what it claims.
- **Linux GNU sed:** `paths_file` contains extracted gate paths. Path
  uniqueness check fails because `gate_worktree_cleanliness_v1.sh` is
  invoked 8 times (begin/assert.../end stateful contract pattern). The
  multi-invocation is intentional — the gate has three command verbs
  (begin, assert, end) and is structurally designed to be called
  multiple times across a CI run.

Even with the regex fixed (replacing `\b` with portable character-class
boundaries), the uniqueness check is structurally incompatible with
stateful gates. Patching it with an exception list would create a
maintenance burden (every future stateful gate would need to be added),
and no future stateful gate has a way to declare its intent except via
the exception list — pure gate-side knowledge encoded in a different
gate.

### Check 3 (banner uniqueness) — works, kept

The banner-duplicate check uses grep on literal `=== Gate: ... ===`
patterns. No regex word-boundary issues. Catches accidental copy/paste
of gate banner echo lines. Real value, fully portable.

---

## Edit shape

Single file changed: `scripts/gate_prove_ci_structure_canonical_v1.sh`.

  - Removed: 50 lines (path extraction, uniqueness check, ordering
    check, related tempfiles + cleanup).
  - Kept: banner-uniqueness check, plus all the file/path setup
    boilerplate, plus `LC_ALL=C` envelope.
  - Updated: header comments to document why the two checks were
    removed (the explanation above, condensed inline).

Net delta: 100 lines → 50 lines (net −50 lines, 25 insertions / 75
deletions, the inserts being the new explanatory comments).

The gate's purpose ("structure canonical") is unchanged in name —
banner-uniqueness IS a structural check. The narrower scope is honest:
the previous "structure" implied per-path invariants the gate couldn't
actually enforce.

---

## Validation

- `ruff src/`: clean.
- `mypy src/squadvault/core/`: clean.
- Gate passes standalone under `LC_ALL=C` (Linux behavior).
- Gate passes standalone under simulated macOS shell
  (`env -i ... LANG=en_US.UTF-8 bash <gate>`) — Finding D's envelope
  pattern works here too because the banner check uses no
  locale-sensitive primitives, but `LC_ALL=C` is set explicitly for
  consistency.
- 8 affected parity gates still pass.

No fingerprint regeneration needed. The surface-freeze fingerprint is
computed from `prove_ci.sh` content + Index block + Labels TSV. None of
those changed. Only one gate file's content changed, which is not in
the fingerprint surface.

---

## prove_ci.sh ERROR-line delta (clean tree, projected)

Pre (commit `dc2b2bf`): 1 ERROR (env export-assemblies).

Post-this-commit: 1 ERROR (unchanged).

The structure_canonical gate has been failing rc=1 silently in
prove_ci.sh's invocation since the cluster was first surfaced; that
silent failure was masked by missing `set -e` in prove_ci.sh (Finding
B mechanism). Removing the broken checks doesn't change the visible
ERROR count because the gate's failure was already invisible. What
changes:

  - **rc of `gate_prove_ci_structure_canonical_v1.sh` standalone:**
    previously rc=1 on Linux (false-positive) and rc=0 on Mac
    (false-negative). Now rc=0 on both.
  - **silent-red gate count in prove_ci.sh:** previously 1 (this gate).
    Now 0.

This is the milestone the F3/F6/F-D/C+E retirement work was driving
toward. **Finding B mechanism closure (`set -euo pipefail` addition to
`prove_ci.sh`) is now safe to land** — there is no pre-existing
silent-rc=1 gate for it to expose.

---

## Path forward — Finding B mechanism closure

After this commit lands and is verified clean (rc=0, ERROR=1, all
ERRORs accounted for as env-only), the next commit can add `set -euo
pipefail` to `prove_ci.sh` and confirm it lands without exposing new
failures. That's Finding B mechanism closure proper.

Recommended next-session sequence:

  1. Add `set -euo pipefail` to `prove_ci.sh` (after the existing
     `export LC_ALL=C` etc. envelope at lines 8-11).
  2. Run `bash scripts/prove_ci.sh` on clean tree.
  3. Confirm rc=0 with the same ERROR count (1, env-only).
  4. If anything else fails, roll back and triage (no new findings
     should appear, but a low-probability environmental issue is
     possible).
  5. Push.
  6. Update the F-series triage memo to retire Finding B mechanism
     entirely.

---

## Findings still open after this commit

  - F7 §finding memo amendment — pending bullets accumulated.
  - export-assemblies env ERROR — environmental triage, separate scope.
  - `_status.sh` and `gate_contract_linkage_v1.sh` No-such-file lines
    — second resolves with unpushed `9404659`.
  - Hygiene bundle `9404659` — items 1, 3, 5 still pending; item 4
    subsumed by `70e4003`.
  - **Finding B mechanism closure** — now unblocked (this commit).

---

## Cross-references

- Finding B triage memo: `_observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md`
- F3 memo (Finding B first surfaced post-triage): `_observations/OBSERVATIONS_2026_04_27_F3_RETIREMENT_AND_AUTOSYNC_RESIDUE.md`
- Finding D memo (Finding B's portability bug class first named):
  `_observations/OBSERVATIONS_2026_04_27_FINDING_D_LC_ALL_PORTABILITY.md`
- Findings C+E memo (closed three more siblings of the same dormant
  cluster): `_observations/OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md`
