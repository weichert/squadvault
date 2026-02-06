#!/usr/bin/env bash
set -euo pipefail

echo "== Local shell hygiene (v1) =="
echo "NOTE: local-only helper (NOT invoked by CI)."
echo

# 1) Verify bash can run with nounset safely (common failure mode from startup/teardown scripts)
echo "==> bash nounset smoke test"
bash -lc 'set -u; : "${HISTTIMEFORMAT?ok}"; : "${size?ok}"; echo "OK: HISTTIMEFORMAT+size defined under set -u"'

# 2) Print where the guards are expected to live (informational)
echo
echo "==> expected guard markers"
for f in "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.bash_logout"; do
  if [[ -f "$f" ]]; then
    if grep -n "SV_NOUNSET_GUARDS_V1" "$f" >/dev/null 2>&1; then
      echo "OK: found SV_NOUNSET_GUARDS_V1 in $f"
    fi
  fi
done

echo
echo "OK: local shell hygiene checks passed."
