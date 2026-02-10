from __future__ import annotations

from pathlib import Path

PROVE_CI = Path("scripts/prove_ci.sh")

NEEDLE = "bash scripts/prove_contract_surface_completeness_v1.sh"
INSERT = "bash scripts/prove_contract_surface_autosync_noop_v1.sh"

def main() -> int:
    if not PROVE_CI.exists():
        raise SystemExit(f"FAIL: missing {PROVE_CI}")

    s = PROVE_CI.read_text(encoding="utf-8")

    if INSERT in s:
        print("OK: prove_ci already calls autosync no-op proof.")
        return 0

    if NEEDLE not in s:
        raise SystemExit(
            "FAIL: could not find insertion anchor in scripts/prove_ci.sh.\n"
            f"Expected to find line containing:\n  {NEEDLE}\n"
            "Refusing to patch to avoid incorrect placement."
        )

    # Insert immediately after the first occurrence of the completeness proof call.
    lines = s.splitlines(True)
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if (not inserted) and (NEEDLE in line):
            # Preserve indentation if present
            prefix = line.split("bash", 1)[0]
            out.append(f"{prefix}{INSERT}\n")
            inserted = True

    if not inserted:
        raise SystemExit("FAIL: internal error: insertion not performed.")

    PROVE_CI.write_text("".join(out), encoding="utf-8")
    print("OK: inserted autosync no-op proof call into prove_ci.sh.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
