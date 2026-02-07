# Canonical Patcher / Wrapper Pattern (v1.0)

**Status:** Canonical  
**Applies To:** All operational, CI, and documentation mutations  
**Audience:** Engineers, operators, tired humans at 2am

---

## Why This Pattern Exists

This pattern exists to keep SquadVault safe, repeatable, and boring in the best way.

It prevents:
- Unsafe one-off shell edits
- Non-idempotent changes
- CI-only failures caused by environment drift

Every change becomes explicit, replayable, reviewable, and safe.

---

## The Two Files (Always Both)

Every change uses a **pair**:

1. **Patcher (Python)** — applies the mutation  
2. **Wrapper (Bash)** — runs and verifies it  

Neither is optional.

---

## Reference Implementation

- `scripts/_patch_example_noop_v1.py`
- `scripts/patch_example_noop_v1.sh`

Copy this pattern. Do not improve it.

---

## What “Step 2: Run Patcher” Means

> Execute the Python file that applies the change.

Nothing more.

---

## Hard Warning

Never type Python directly into the shell.

If it matters, it gets a patcher.

---

## Bash Compatibility

Wrappers must work under **Bash 3.2**.
