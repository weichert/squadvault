from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: no_obsolete_allowlist_rewrite_artifacts (v1) begin\n"
END   = "# SV_GATE: no_obsolete_allowlist_rewrite_artifacts (v1) end\n"

BLOCK = (
    BEGIN
    "bash scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh\n"
    END
)

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        # already wired (idempotent)
        return

    # Insert near other early gates (after allowlist insert-sorted gate is fine).
    anchor = "bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh\n"
    if anchor not in text:
        raise SystemExit("ERROR: cannot find anchor allowlist gate line in prove_ci.sh")

    new_text = text.replace(anchor, anchor + BLOCK)
    PROVE.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
