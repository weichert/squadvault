from __future__ import annotations

from pathlib import Path

CHECK = Path("scripts/check_ci_proof_surface_matches_registry_v1.sh")

INSERT_ANCHOR = 'done < "${registry}"\n\nif [[ -z "${registry_list}" ]]; then'

INSERT_BLOCK = """done < "${registry}"

# Marker mode: parse the bounded section using the same strict registry entry grammar.
if [[ "${in_marker_block}" == "1" ]]; then
  while IFS= read -r mline; do
    # required format: "- scripts/prove_...sh — purpose"
    if [[ "${mline}" =~ ^-\\ (scripts/prove_[A-Za-z0-9_]+\\.sh)\\ —\\  ]]; then
      path="${BASH_REMATCH[1]}"
      registry_list+="${path}"$'\\n'
    elif [[ "${mline}" =~ ^-\\  ]]; then
      echo "ERROR: registry entry malformed (expected '- scripts/prove_*.sh — ...'):" >&2
      echo "  ${mline}" >&2
      exit 1
    fi
  done <<< "${registry_section}"
fi

if [[ -z "${registry_list}" ]]; then"""

def main() -> None:
    if not CHECK.exists():
        raise SystemExit(f"ERROR: missing {CHECK}")

    text = CHECK.read_text(encoding="utf-8")

    # Idempotence
    if "Marker mode: parse the bounded section using the same strict registry entry grammar." in text:
        print("OK: marker-mode registry_list derivation already present (v6 idempotent).")
        return

    if INSERT_ANCHOR not in text:
        raise SystemExit("ERROR: could not find insertion anchor near registry_list emptiness check (unexpected shape).")

    text2 = text.replace(INSERT_ANCHOR, INSERT_BLOCK, 1)
    CHECK.write_text(text2, encoding="utf-8")
    print("OK: added marker-mode registry_list derivation (v6).")

if __name__ == "__main__":
    main()
