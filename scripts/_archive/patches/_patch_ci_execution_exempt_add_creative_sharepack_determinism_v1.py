from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CI_EXECUTION_EXEMPT_v1_BEGIN -->"
END   = "<!-- SV_CI_EXECUTION_EXEMPT_v1_END -->"

ITEM = "- scripts/prove_creative_sharepack_determinism_v1.sh"

def main() -> None:
    s = DOC.read_text(encoding="utf-8")

    if BEGIN not in s or END not in s:
        raise SystemExit("ERROR: exemption markers not found; refusing to patch blindly")

    pre, rest = s.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    lines = [ln.rstrip("\n") for ln in mid.splitlines()]
    kept: list[str] = []
    for ln in lines:
        t = ln.strip()
        if not t:
            continue
        kept.append(t)

    if ITEM in kept:
        print("OK: already exempt (noop)")
        return

    kept.append(ITEM)
    kept = sorted(set(kept), key=lambda x: x)

    new_mid = "\n" + "\n".join(kept) + "\n"
    out = pre + BEGIN + new_mid + END + post
    DOC.write_text(out, encoding="utf-8", newline="\n")
    print("OK")

if __name__ == "__main__":
    main()
