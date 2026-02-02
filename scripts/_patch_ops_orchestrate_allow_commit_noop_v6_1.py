#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

OPS = Path("scripts/ops_orchestrate.sh")

def main() -> None:
    s = OPS.read_text(encoding="utf-8")

    # We require the legacy pattern to exist exactly once:
    needle = 'die "--commit requested but no changes occurred"'
    if s.count(needle) != 1:
        raise SystemExit(f"ERROR: expected exactly 1 occurrence of {needle!r}, found {s.count(needle)}")

    # Also require the commit banner to exist (to anchor where we inject an else)
    banner = 'echo "=== Commit (explicit) ==="'
    if banner not in s:
        raise SystemExit(f"ERROR: could not find commit banner {banner!r}")

    # Find the inner if-block that currently dies on no-op, and replace it
    # with a no-op skip that wraps the commit section in an else.
    #
    # BEFORE (shape):
    #   if [[ "${pass1_changed}" != "1" ]]; then
    #     die "--commit requested but no changes occurred"
    #   fi
    #
    #   echo
    #   echo "=== Commit (explicit) ==="
    #
    # AFTER:
    #   if [[ "${pass1_changed}" != "1" ]]; then
    #     echo "OK: --commit requested but no changes occurred (no-op); skipping commit"
    #   else
    #     echo
    #     echo "=== Commit (explicit) ==="
    #     ...
    #   fi
    #
    # We do this by:
    # 1) rewriting the die-block into an if/else opener
    # 2) inserting a closing "  fi" just before the outer commit-enabled fi
    #
    # To keep this robust, we:
    # - replace the exact 3-line die-block
    # - add an "else" immediately before the first commit-banner echo line

    die_block = (
        '  if [[ "${pass1_changed}" != "1" ]]; then\n'
        '    die "--commit requested but no changes occurred"\n'
        '  fi\n'
    )
    if die_block not in s:
        raise SystemExit("ERROR: could not find expected 3-line die block (format drift)")

    s2 = s.replace(
        die_block,
        (
            '  if [[ "${pass1_changed}" != "1" ]]; then\n'
            '    echo "OK: --commit requested but no changes occurred (no-op); skipping commit"\n'
            '  else\n'
        ),
        1,
    )

    # Now we need to close the else with "  fi" before the outer "fi" that closes commit_enabled.
    # We insert that right before the line that starts the Prove section, because commit block
    # must finish before proving.
    #
    # Find the first Prove header line.
    prove_idx = s2.find('echo "=== Prove: scripts/prove_ci.sh ==="')
    if prove_idx == -1:
        # Some versions echo without quotes; try looser match
        prove_idx = s2.find("=== Prove: scripts/prove_ci.sh ===")
    if prove_idx == -1:
        raise SystemExit('ERROR: could not find Prove header "=== Prove: scripts/prove_ci.sh ===" (format drift)')

    # Back up to the start of the line containing the prove header
    line_start = s2.rfind("\n", 0, prove_idx) + 1

    # Immediately before Prove, we should be exiting the commit_enabled block with a lone "fi".
    # We will insert "  fi" (closing the else) just before that outer fi.
    #
    # Find the last occurrence of "\nfi\n" before the prove header (this is expected to be the commit_enabled closer).
    outer_fi_pos = s2.rfind("\nfi\n", 0, line_start)
    if outer_fi_pos == -1:
        raise SystemExit("ERROR: could not find outer fi before Prove header (format drift)")

    # Insert the closing "  fi" just before that outer fi.
    insertion_point = outer_fi_pos + 1  # keep leading newline
    s3 = s2[:insertion_point] + "  fi\n" + s2[insertion_point:]

    # Now ensure we also re-add the commit banner lines under the else.
    # We already opened 'else', but we haven't duplicated anything; instead we need to ensure
    # the commit banner is still present and now falls under the else branch.
    #
    # To do that, we must ensure we inserted "else" right before the commit section begins.
    # We opened else where the die-block used to be, but the commit banner is still below; good.

    OPS.write_text(s3, encoding="utf-8")
    print("OK: patched ops_orchestrate to treat --commit no-op as OK (v6.1).")

if __name__ == "__main__":
    main()
