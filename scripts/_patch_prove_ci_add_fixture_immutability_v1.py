#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

PROVE_CI = Path("scripts/prove_ci.sh")

BLOCK = r'''
# --- Fixture immutability guard (CI) ---
# We forbid proofs from mutating committed fixtures (especially fixture DBs).
# This is a LOUD early failure to prevent masked nondeterminism.
STATEFILE="$(mktemp "${TMPDIR:-/tmp}/squadvault_fixture_state.XXXXXX")"
cleanup_fixture_state() { rm -f "${STATEFILE}" >/dev/null 2>&1 || true; }
trap cleanup_fixture_state EXIT

# Collect fixture files used by CI proofs.
# - Always include the known CI DB fixture.
# - Also include any top-level sqlite fixtures (if present) to catch drift.
fixture_files=("fixtures/ci_squadvault.sqlite")
for f in fixtures/*.sqlite; do
  if [[ -f "${f}" ]]; then
    # avoid duplicate if fixtures/ci_squadvault.sqlite matches the glob
    if [[ "${f}" != "fixtures/ci_squadvault.sqlite" ]]; then
      fixture_files+=("${f}")
    fi
  fi
done

./scripts/check_fixture_immutability_ci.sh record "${STATEFILE}" "${fixture_files[@]}"
# --- /Fixture immutability guard (CI) ---

'''.strip("\n")

VERIFY_SNIPPET = r'''
# --- Fixture immutability guard (CI) ---
./scripts/check_fixture_immutability_ci.sh verify "${STATEFILE}" "${fixture_files[@]}"
# --- /Fixture immutability guard (CI) ---
'''.strip("\n")


def main() -> None:
    if not PROVE_CI.exists():
        raise SystemExit(f"ERROR: missing {PROVE_CI}")

    s = PROVE_CI.read_text(encoding="utf-8")

    if "check_fixture_immutability_ci.sh" in s:
        print("OK: prove_ci.sh already contains fixture immutability guard.")
        return

    lines = s.splitlines()

    # Insert the RECORD block after we cd to repo root if possible.
    insert_idx = None
    for i, line in enumerate(lines):
        # common shapes we expect in shims/ops scripts
        if "cd" in line and "REPO_ROOT" in line:
            insert_idx = i + 1
            break

    if insert_idx is None:
        # fallback: after shebang line
        insert_idx = 1 if lines and lines[0].startswith("#!") else 0

    # Insert VERIFY at the end, but before a final "OK" echo if present.
    # We prefer verify AFTER all proofs have run.
    verify_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("echo ") and "OK" in lines[i]:
            verify_idx = i
            break

    new_lines = []
    new_lines.extend(lines[:insert_idx])
    new_lines.append(BLOCK)
    new_lines.extend(lines[insert_idx:verify_idx])
    new_lines.append("")
    new_lines.append(VERIFY_SNIPPET)
    new_lines.extend(lines[verify_idx:])

    PROVE_CI.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("OK: patched scripts/prove_ci.sh with fixture immutability guard.")


if __name__ == "__main__":
    main()
