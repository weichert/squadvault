# Pre-Commit Gate: docs/ Map Registration (v1)
## SquadVault | Reset Memo Follow-On

**Date:** 2026-05-16
**HEAD at authoring:** `a548787` (Map v1.7 provisional section patch)
**Filing:** `_observations/OBSERVATIONS_2026_05_16_PRECOMMIT_GATE_DOCS_MAP_REGISTRATION.md`
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**Predecessor:** Reset Memo v1.0 at `bb0f325` (section 6.3 names this gate as
a follow-on engineering task; section 10.2 names it as a standing backlog item).

**Output:** Gate script `scripts/gate_docs_map_registration_v1.sh` added;
wired into the tracked pre-commit hook at `scripts/git-hooks/pre-commit_v1.sh`;
five gate tests added at `Tests/test_docs_map_registration_gate_v1.py`. The
hook docstring is corrected to remove the reference to the archived installer.

---

## 1. What was built

**Gate script:** `scripts/gate_docs_map_registration_v1.sh`

Fires when any new file with a binding-doc extension (.md, .docx, .pdf) is
staged directly in `docs/` (not in a subdirectory). If no Documentation Map
version (`docs/SquadVault_Documentation_Map_v*.{md,docx}`) or patch addendum
(`docs/map_patch_*.md`) is also staged in the same set, the commit fails with
a clear error message naming the unaccompanied file(s) and offering two remedies:
(1) stage a Map modification or patch addendum in the same commit, or (2) file
the document in `_observations/` if it is provisional.

Subdirectory additions (`docs/templates/`, `docs/80_indices/`, etc.) are not
caught -- those are support artifacts, not top-level binding doctrine.

**Pre-commit hook update:** `scripts/git-hooks/pre-commit_v1.sh`

The new gate is added as gate 4 (after repo-root allowlist, before the final
OK line). The hook docstring is corrected: the reference to the archived installer
(`scripts/install_git_hooks_v1.sh`) is replaced with the accurate current pattern
(manual `cp`). This resolves Finding 1 from
`OBSERVATIONS_2026_04_20_PRECOMMIT_GATE_PARITY_DEFERRED_FINDINGS.md`.

**Tests:** `Tests/test_docs_map_registration_gate_v1.py` (5 tests)

- `test_gate_script_exists` -- gate script is present at the expected path
- `test_gate_script_is_executable` -- gate script has executable bit set
- `test_gate_wired_into_pre_commit_hook` -- tracked hook invokes the gate
- `test_no_unregistered_top_level_docs_files` -- every current top-level docs/
  file is in the known-good allowlist (catches future bypass via SV_SKIP_PRECOMMIT)
- `test_grandfathered_files_still_exist` -- expected persistent Map files are
  still present (catches renames that would break the allowlist)

---

## 2. What is NOT in scope

**ruff/mypy/pytest as pre-commit gates** -- the Roadmap section 5 hardening item.
Not implemented. Pytest takes ~8 minutes per run; adding it to the pre-commit hook
would make every commit impractical. The existing session discipline (manual gate
before commit, separate paste turns) is the correct pattern. That item remains a
standing background item with no scheduled session.

**Automated hook installation** -- the installer was deliberately archived.
The current pattern (manual `cp`) is correct for a single-developer repo. The
hook docstring is updated to describe reality; no new installer is built.

**Finding 2 from the prior parity memo** (`gate_ci_guardrails_ops_entrypoints_section_v2.sh`
fails at pristine HEAD) -- out of scope. Requires archaeology; separate session.

---

## 3. Installation note (ACTION REQUIRED)

The tracked hook at `scripts/git-hooks/pre-commit_v1.sh` is updated, but the
installed hook at `.git/hooks/pre-commit` is not tracked by git and must be
reinstalled manually after this commit lands:

    cp scripts/git-hooks/pre-commit_v1.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit

Until that command runs, commits will show three gates (banner-paste, no-xtrace,
repo-root allowlist) rather than four. The gate test suite will pass regardless
(it tests the tracked hook, not the installed hook).

---

## 4. Gate results

- Ruff: zero errors (68 source files)
- Mypy: no issues found (68 source files)
- Tests: 2227 passed / 3 skipped (+5 vs prior baseline of 2222/3)

---

## 5. Cross-references

- `bb0f325` -- Reset Memo v1.0 (section 6.3: gate specification; section 10.2: backlog)
- `a548787` -- HEAD at session start (Map v1.7 provisional section patch)
- `OBSERVATIONS_2026_04_20_PRECOMMIT_GATE_PARITY_DEFERRED_FINDINGS.md` -- Finding 1
  resolved by this session; Finding 2 deferred
- `scripts/gate_docs_map_registration_v1.sh` -- gate script (this commit)
- `scripts/git-hooks/pre-commit_v1.sh` -- tracked hook (this commit)
- `Tests/test_docs_map_registration_gate_v1.py` -- gate tests (this commit)
