# SquadVault — Rules of Engagement (Repo Process)

**Status:** Canonical operating practice  
**Purpose:** Reduce mistakes, increase speed, preserve auditability

## Core Principle

**Prefer scripts with proper wrappers for changes rather than manual edits.**

We make changes via repeatable, reviewable scripts that:
- fail fast if assumptions aren’t met
- emit clear evidence of what changed
- are easy to re-run (or safely refuse)

Manual edits are allowed for small text tweaks, but anything that touches:
- schema alignment
- renames / refactors
- cross-file changes
- contract/spec compliance
- test stabilization

…should default to **script-first**.

## Standard Workflow

1) **Diagnose**
- identify root cause (schema mismatch, naming drift, ordering non-determinism, etc.)
- locate all call sites (ripgrep)

2) **Patch via script**
- write a patch script under `scripts/_patch_*.py`
- wrap it in `scripts/*.sh` (stable entrypoint)
- keep patch scripts narrow: one concern per script

3) **Verify**
- run tests via wrapper (prefer repo-standard invocations)
- capture outputs in terminal history / PR notes

4) **Commit**
- commit the script + changes together
- commit message should mention what was enforced (e.g., “Align ExcludedSignal construction to schema (details[])”)

## Wrapper Requirements (Non-Negotiable)

Every operational script wrapper should:
- use `set -euo pipefail`
- run from repo root
- print key context (repo_root, python version)
- produce a “what to do next” hint (e.g., `git diff`, `pytest`)

## Patch Script Requirements

Patch scripts should:
- be safe to re-run
- refuse to proceed if expected “needles” are missing
- print:
  - which files were changed
  - how many replacements were made
  - what the expected verification command is

## Evidence Standard

A good patch run outputs:
- counts of changes
- file list
- “Review with git diff”
- “Verify with tests”

## Example: Schema Alignment Fix

When schema says `details: list[ReasonDetailKV]`:
- do not use `detail=...`
- normalize to `details=[ReasonDetailKV(...)]` with deterministic ordering (sort keys)

## When Manual Edits Are OK

Manual edits are acceptable when:
- it’s a single-file prose change
- no structural refactor is involved
- the change is trivially reviewable
- no other files must be updated to stay consistent

If you catch yourself editing 2+ files manually: **stop** and write a script.

## Change Ownership

If a change affects:
- contracts / schemas
- ingestion/canonicalization
- selection logic
- export formatting guarantees

…treat it as “high risk” and apply the strictest script-first workflow.

---

**This document formalizes the repo process:**
> Script-first + wrappers-first is the default operating mode for SquadVault.
