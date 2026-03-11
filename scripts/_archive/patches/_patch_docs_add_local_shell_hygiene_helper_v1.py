from __future__ import annotations

from pathlib import Path

INDEX  = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
HELPER = Path("scripts/prove_local_shell_hygiene_v1.sh")


def _helper_body() -> str:
    return """#!/usr/bin/env bash
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
"""


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing index: {INDEX}")

    HELPER.write_text(_helper_body(), encoding="utf-8")
    HELPER.chmod(0o755)

    txt = INDEX.read_text(encoding="utf-8")

    # Link it under Local-only helpers (not invoked by CI). Keep it clearly labeled.
    # We do not create a doc for this helper; it's intentionally a local tool.
    line = "- `scripts/prove_local_shell_hygiene_v1.sh` — local-only helper: validates bash nounset startup/teardown safety (SV_NOUNSET_GUARDS_V1)\n"

    if line in txt:
        return

    section = "## Local-only helpers (not invoked by CI)\n"
    if section not in txt:
        if not txt.endswith("\n"):
            txt += "\n"
        txt += "\n" + section

    before, after = txt.split(section, 1)
    if not after.startswith("\n"):
        after = "\n" + after
    txt = before + section + line + after

    INDEX.write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
