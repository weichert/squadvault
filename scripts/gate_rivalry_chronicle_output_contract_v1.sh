#!/usr/bin/env bash
set -euo pipefail

# SquadVault — Rivalry Chronicle Output Contract Gate (v1)
# Validates exported Rivalry Chronicle markdown conforms to contract v1.

fail() { echo "RIVALRY_CHRONICLE_CONTRACT_V1_FAIL: $*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

CONTRACT="docs/contracts/rivalry_chronicle_output_contract_v1.md"
[[ -f "${CONTRACT}" ]] || fail "missing contract doc: ${CONTRACT}"

# Allow caller to point at a specific export file (e.g. from prove script).
# Otherwise, search common export roots for the approved_latest file.
target="${1:-}"

if [[ -z "${target}" ]]; then
  # Prefer artifacts/exports (tracked) but allow temp export dirs too.
  target="$(find artifacts -type f -name 'rivalry_chronicle_v1__approved_latest.md' 2>/dev/null | head -n1 || true)"
fi

[[ -n "${target}" ]] || fail "could not locate rivalry_chronicle_v1__approved_latest.md (pass path as arg to gate)"
[[ -f "${target}" ]] || fail "missing target file: ${target}"

# Read basic checks
# 1) Starts with required title
head -n 1 "${target}" | grep -Fx "# Rivalry Chronicle (v1)" >/dev/null || fail "first line must be: # Rivalry Chronicle (v1)"

# 2) Metadata keys present (within first 60 lines for robustness)
head -n 60 "${target}" | grep -E '^League:\s*.+$' >/dev/null || fail "missing metadata key: League:"
head -n 60 "${target}" | grep -E '^Season:\s*[0-9]+$' >/dev/null || fail "missing/invalid metadata key: Season:"
head -n 60 "${target}" | grep -E '^Week:\s*[0-9]+$' >/dev/null || fail "missing/invalid metadata key: Week:"
head -n 60 "${target}" | grep -E '^State:\s*APPROVED$' >/dev/null || fail "missing/invalid metadata key: State: APPROVED"
head -n 60 "${target}" | grep -E '^Artifact Type:\s*RIVALRY_CHRONICLE_V1$' >/dev/null || fail "missing/invalid metadata key: Artifact Type: RIVALRY_CHRONICLE_V1"

# 3) Required sections exist (in order)
# Use awk to enforce ordering by tracking first occurrence line numbers
ms="$(grep -n '^## Matchup Summary' "${target}" | head -n1 | cut -d: -f1 || true)"
km="$(grep -n '^## Key Moments' "${target}" | head -n1 | cut -d: -f1 || true)"
sn="$(grep -n '^## Stats & Nuggets' "${target}" | head -n1 | cut -d: -f1 || true)"
cl="$(grep -n '^## Closing' "${target}" | head -n1 | cut -d: -f1 || true)"

[[ -n "${ms}" && -n "${km}" && -n "${sn}" && -n "${cl}" ]] || fail "missing required section headings (Matchup Summary / Key Moments / Stats & Nuggets / Closing)"
# numeric compare (bash3 safe)
if ! ( [[ "${ms}" -lt "${km}" ]] && [[ "${km}" -lt "${sn}" ]] && [[ "${sn}" -lt "${cl}" ]] ); then
  fail "required section headings are not in required order"
fi

# 4) Disallowed patterns
grep -n "(autofill)" "${target}" >/dev/null && fail "contains autofill placeholders"
grep -n "^{'.*'}$" "${target}" >/dev/null && fail "contains raw python dict repr debug lines"
grep -nE '^/[^[:space:]]+' "${target}" >/dev/null && fail "contains absolute filesystem paths"

echo "OK: Rivalry Chronicle outputs conform to Output Contract (v1)"
