from __future__ import annotations

from pathlib import Path

CHECK = Path("scripts/check_ci_proof_surface_matches_registry_v1.sh")
REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
END = "<!-- CI_PROOF_RUNNERS_END -->"

# The *actual* heading string the check script matches today:
LEGACY_HEADING = "## Proof Runners (invoked by scripts/prove_ci.sh)"

def add_registry_markers() -> bool:
    if not REGISTRY.exists():
        raise SystemExit(f"ERROR: missing {REGISTRY}")
    text = REGISTRY.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        return False

    if LEGACY_HEADING not in text and "## Proof Runners" not in text:
        raise SystemExit(
            "ERROR: could not find Proof Runners heading in registry doc.\n"
            f"Expected: {LEGACY_HEADING} or '## Proof Runners'"
        )

    # Prefer wrapping the legacy heading section if present, else generic heading.
    heading = LEGACY_HEADING if LEGACY_HEADING in text else "## Proof Runners"

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_section = False
    opened = False

    for line in lines:
        if line.strip() == heading and not opened:
            out.append(line)
            out.append("\n")
            out.append(BEGIN + "\n")
            in_section = True
            opened = True
            continue

        if in_section and line.startswith("## "):
            out.append(END + "\n\n")
            in_section = False

        out.append(line)

    if in_section:
        out.append("\n" + END + "\n")

    REGISTRY.write_text("".join(out), encoding="utf-8")
    return True

def harden_check_script() -> bool:
    if not CHECK.exists():
        raise SystemExit(f"ERROR: missing {CHECK}")

    text = CHECK.read_text(encoding="utf-8")
    if "CI_PROOF_RUNNERS_BEGIN" in text and "CI_PROOF_RUNNERS_END" in text:
        return False

    # Insert marker-aware parse just above the existing legacy Proof Runners parsing block.
    # We anchor on the comment you showed: "# --- Parse registry: only the Proof Runners section ---"
    anchor = "# --- Parse registry: only the Proof Runners section ---"
    if anchor not in text:
        raise SystemExit(f"ERROR: could not find anchor in check script: {anchor}")

    insert = f"""{anchor}
# Prefer bounded marker block in registry to avoid heading drift.
# Backward compatible: if markers absent, fall back to legacy heading parse.
in_marker_block=0
if grep -q "CI_PROOF_RUNNERS_BEGIN" "${{registry}}" && grep -q "CI_PROOF_RUNNERS_END" "${{registry}}"; then
  in_marker_block=1
fi

"""

    # Replace the first occurrence of the anchor line with our expanded block.
    text2 = text.replace(anchor, insert, 1)

    # Now adjust the legacy loop behavior:
    # - If in_marker_block==1, parse between markers (ignore headings).
    # - Else, run existing heading-based parse unchanged.
    #
    # We patch minimally by injecting marker checks inside the existing while-read loop.
    #
    # We require these sentinels to exist so we can patch safely:
    #   if [[ "${line}" == "## Proof Runners (invoked by scripts/prove_ci.sh)" ]]; then
    sentinel = 'if [[ "${line}" == "## Proof Runners (invoked by scripts/prove_ci.sh)" ]]; then'
    if sentinel not in text2:
        raise SystemExit("ERROR: could not find legacy heading sentinel in check script (unexpected shape).")

    # Inject marker gating just before the sentinel.
    inject_before = """  # Marker mode: capture lines strictly between markers
  if [[ "${in_marker_block}" == "1" ]]; then
    if [[ "${line}" == *"CI_PROOF_RUNNERS_BEGIN"* ]]; then
      in_section=1
      continue
    fi
    if [[ "${line}" == *"CI_PROOF_RUNNERS_END"* ]]; then
      in_section=0
      break
    fi
    if [[ "${in_section}" == "1" ]]; then
      echo "${line}"
    fi
    continue
  fi

"""

    text3 = text2.replace(sentinel, inject_before + sentinel, 1)

    CHECK.write_text(text3, encoding="utf-8")
    return True

def main() -> None:
    changed = False
    changed |= add_registry_markers()
    changed |= harden_check_script()

    if changed:
        print("OK: registry markers added + check script hardened (v3).")
    else:
        print("OK: registry markers + hardening already canonical (v3).")

if __name__ == "__main__":
    main()
