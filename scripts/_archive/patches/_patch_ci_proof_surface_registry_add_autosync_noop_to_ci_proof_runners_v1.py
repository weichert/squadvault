from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
END = "<!-- CI_PROOF_RUNNERS_END -->"

ENTRY = "scripts/prove_contract_surface_autosync_noop_v1.sh"

def main() -> int:
    if not REG.exists():
        raise SystemExit(f"FAIL: missing {REG}")

    s = REG.read_text(encoding="utf-8")

    if BEGIN not in s or END not in s:
        raise SystemExit(
            "FAIL: CI_PROOF_RUNNERS markers not found; refusing to patch.\n"
            f"Expected:\n  {BEGIN}\n  {END}"
        )

    before, rest = s.split(BEGIN, 1)
    middle, after = rest.split(END, 1)

    # Parse the list: one path per line, ignore blanks and comments.
    lines = []
    for ln in middle.splitlines():
        t = ln.strip()
        if not t:
            continue
        if t.startswith("<!--") and t.endswith("-->"):
            continue
        lines.append(t)

    if ENTRY in lines:
        print("OK: CI_PROOF_RUNNERS already contains autosync no-op proof.")
        return 0

    lines.append(ENTRY)

    # Deterministic: unique + sorted.
    lines_sorted = sorted(set(lines), key=lambda x: x)

    middle_out = "\n" + "\n".join(lines_sorted) + "\n"

    out = before + BEGIN + middle_out + END + after
    REG.write_text(out, encoding="utf-8")

    print("OK: inserted autosync no-op proof into CI_PROOF_RUNNERS (sorted).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
