from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_PROOF_SURFACE_REGISTRY_TOOLING_v1_BEGIN -->"
END = "<!-- SV_CI_PROOF_SURFACE_REGISTRY_TOOLING_v1_END -->"

ANCHOR_MARKER = "<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->"

BLOCK = f"""{BEGIN}
# - Helpers: CI Proof Surface Registry
- scripts/patch_ci_proof_surface_registry_register_ci_proof_runner_v1.sh — Register a CI proof runner into the registry blocks (strict, sorted, fail-closed).
- scripts/doctor_ci_proof_surface_registry_v1.sh — Diagnose CI Proof Surface Registry structural invariants (check/fix modes) (v1).
{END}
"""

def main() -> int:
    if not DOC.exists():
        raise SystemExit(f"FAIL: missing {DOC}")

    s = DOC.read_text(encoding="utf-8")

    if BEGIN in s and END in s:
        # ensure canonical block content (exact replace)
        pre = s.split(BEGIN, 1)[0]
        rest = s.split(BEGIN, 1)[1]
        mid, post = rest.split(END, 1)
        out = pre + BLOCK + post
        if out == s:
            print("OK: ops index already contains CI proof registry tooling block (v1).")
            return 0
        DOC.write_text(out, encoding="utf-8")
        print("OK: refreshed CI proof registry tooling block to canonical content (v1).")
        return 0

    if ANCHOR_MARKER not in s:
        raise SystemExit(
            "FAIL: anchor marker not found in ops index; refusing to guess insertion point.\n"
            f"Expected to find: {ANCHOR_MARKER}"
        )

    lines = s.splitlines(True)
    out_lines: list[str] = []
    inserted = False

    for i, ln in enumerate(lines):
        out_lines.append(ln)
        if not inserted and ANCHOR_MARKER in ln:
            # insert AFTER the anchor marker line
            out_lines.append("\n" if (out_lines and not out_lines[-1].endswith("\n")) else "")
            out_lines.append(BLOCK + ("\n" if not BLOCK.endswith("\n") else ""))
            inserted = True

    if not inserted:
        raise SystemExit("FAIL: internal error: insertion did not occur.")

    out = "".join(out_lines)
    DOC.write_text(out, encoding="utf-8")
    print("OK: inserted CI proof registry tooling discoverability block into ops index (v1).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
