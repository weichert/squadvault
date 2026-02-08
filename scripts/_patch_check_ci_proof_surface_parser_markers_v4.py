from __future__ import annotations

from pathlib import Path

CHECK = Path("scripts/check_ci_proof_surface_matches_registry_v1.sh")

def main() -> None:
    if not CHECK.exists():
        raise SystemExit(f"ERROR: missing {CHECK}")

    text = CHECK.read_text(encoding="utf-8")

    # Idempotence: if we already switched marker-mode to append to registry_section, no-op.
    if "registry_section+=" in text and "registry_section=\"\"" in text:
        print("OK: marker accumulator already canonical (v4 idempotent).")
        return

    # We will:
    # 1) Ensure a registry_section accumulator exists near the parse block.
    # 2) Replace marker-mode echo with registry_section append.
    #
    # Anchor on the block we inserted in v3: "in_marker_block=0"
    anchor = "in_marker_block=0"
    if anchor not in text:
        raise SystemExit("ERROR: missing v3 anchor 'in_marker_block=0' (unexpected).")

    # Insert registry_section init right after in_marker_block logic.
    insert_after = """in_marker_block=0
if grep -q "CI_PROOF_RUNNERS_BEGIN" "${registry}" && grep -q "CI_PROOF_RUNNERS_END" "${registry}"; then
  in_marker_block=1
fi

registry_section=""
"""
    if insert_after not in text:
        # Replace the existing v3 block with the same block plus registry_section init.
        # Do a conservative replace of the exact v3 stanza.
        v3_stanza = """in_marker_block=0
if grep -q "CI_PROOF_RUNNERS_BEGIN" "${registry}" && grep -q "CI_PROOF_RUNNERS_END" "${registry}"; then
  in_marker_block=1
fi

"""
        if v3_stanza not in text:
            raise SystemExit("ERROR: could not find exact v3 stanza to extend (unexpected).")
        text = text.replace(v3_stanza, insert_after, 1)

    # Now change marker-mode capture: replace `echo "${line}"` with append.
    # v3 injected:
    #   if [[ "${in_section}" == "1" ]]; then
    #     echo "${line}"
    #   fi
    old = """    if [[ "${in_section}" == "1" ]]; then
      echo "${line}"
    fi
"""
    new = """    if [[ "${in_section}" == "1" ]]; then
      registry_section+="${line}"$'\\n'
    fi
"""
    if old not in text:
        # If formatting differs slightly, fail closed.
        raise SystemExit("ERROR: could not find marker-mode echo block to replace (unexpected).")
    text = text.replace(old, new, 1)

    # Also ensure legacy mode appends to registry_section (if it currently echoes).
    # The legacy parser likely echoes lines too; we do NOT want to rewrite whole script.
    # We'll opportunistically convert the first legacy echo inside in_section to append if present.
    legacy_old = """    echo "${line}"
"""
    if legacy_old in text and "registry_section+=" not in text:
        text = text.replace(legacy_old, """    registry_section+="${line}"$'\\n'
""", 1)

    # Finally, ensure the emptiness check references registry_section.
    # We replace a common pattern: if [[ -z "${proof_runners}" ]]; then ... with registry_section.
    # If script already uses registry_section, no action.
    if "registry_section" in text:
        # If there is a check like: if [[ -z "${proof_runners}" ]]; then
        text = text.replace('if [[ -z "${proof_runners}" ]]; then', 'if [[ -z "${registry_section}" ]]; then')
        text = text.replace('if [[ -z "${proofs_from_registry}" ]]; then', 'if [[ -z "${registry_section}" ]]; then')

    CHECK.write_text(text, encoding="utf-8")
    print("OK: updated marker/legacy parsing to accumulate into registry_section (v4).")

if __name__ == "__main__":
    main()
