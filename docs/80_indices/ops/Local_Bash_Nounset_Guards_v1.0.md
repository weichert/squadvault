[SV_CANONICAL_HEADER_V1]
Contract Name: Local Bash Nounset Guards
Version: v1.0
Status: CANONICAL

Defers To:
  - Canonical Operating Constitution (Tier 0)
  - CI Guardrails Index (Tier 1) (informational linkage)

Default: Any behavior not explicitly permitted by this contract is forbidden.

—

## Purpose

Some environments/tools execute `bash` under `set -u` (nounset), often indirectly
(e.g., wrappers, CI helpers, shell login/teardown hooks). In those contexts, a
single unbound variable referenced by startup/teardown scripts can crash an
otherwise-correct workflow.

This note standardizes a minimal, explicit guard block for common variables that
have been observed to fail under nounset.

## Scope

This is **local workstation hygiene**, not a repo runtime requirement:

- Applies to: `~/.bashrc`, `~/.bash_profile` (and optionally `~/.profile` if used)
- Does **not** modify repo behavior directly
- Exists to prevent failures like: `-bash: <var>: unbound variable`

## Canonical Guard Block

Add exactly one block (dedupe prior ad-hoc lines) and keep it centralized:

```bash
# SV_NOUNSET_GUARDS_V1: guard common vars to avoid set -u startup/teardown failures
# (Some shells/tools assume these exist; we run with set -u in many wrappers.)
: "${HISTTIMEFORMAT:=}"
: "${size:=}"
```

## Notes

- Keep this block **single-source** (don’t scatter ad-hoc guards across files).
- If you discover additional nounset failures, add them only after confirming the
  variable is commonly assumed by your environment and that defaulting it is safe.

## Verification

```bash
bash -lc 'set -u; : "${HISTTIMEFORMAT?ok}"; : "${size?ok}"; echo "OK: guards survive set -u"'
```
