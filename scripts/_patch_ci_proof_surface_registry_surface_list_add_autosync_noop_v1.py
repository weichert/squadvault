from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->"
END = "<!-- SV_PROOF_SURFACE_LIST_v1_END -->"

SCRIPT = "scripts/prove_contract_surface_autosync_noop_v1.sh"

def _key(line: str) -> str:
    # Sort key based on first occurrence of "scripts/..."
    i = line.find("scripts/")
    if i == -1:
        return line.strip()
    return line[i:].strip()

def main() -> int:
    if not REG.exists():
        raise SystemExit(f"FAIL: missing {REG}")

    s = REG.read_text(encoding="utf-8")

    if BEGIN not in s or END not in s:
        raise SystemExit(
            "FAIL: SV_PROOF_SURFACE_LIST markers not found; refusing to patch.\n"
            f"Expected:\n  {BEGIN}\n  {END}"
        )

    # Fast check: any line containing exact script path
    if SCRIPT in s:
        print("OK: registry already contains autosync no-op proof (somewhere). Proceeding to ensure it's in surface list block.")

    before, rest = s.split(BEGIN, 1)
    middle, after = rest.split(END, 1)

    middle_lines = middle.splitlines()

    # Determine list style from existing entries in this block.
    # Prefer a line that contains "scripts/".
    prefix = ""
    for ln in middle_lines:
        if "scripts/" in ln:
            # keep everything before "scripts/" as the prefix (e.g., "- " or "  - ")
            prefix = ln.split("scripts/", 1)[0]
            break

    # If there are no script lines yet, default to "- " (reasonable, deterministic).
    if prefix == "":
        prefix = "- "

    entry_line = f"{prefix}{SCRIPT}"

    # If already present in this bounded block, no-op.
    for ln in middle_lines:
        if _key(ln) == SCRIPT:
            print("OK: autosync no-op proof already present in SV_PROOF_SURFACE_LIST block.")
            return 0

    # Keep all non-empty lines that look like list entries (contain scripts/),
    # but also preserve any non-list commentary lines as-is (we keep them before the sorted list).
    list_lines: list[str] = []
    other_lines: list[str] = []

    for ln in middle_lines:
        if ln.strip() == "":
            continue
        if "scripts/" in ln:
            list_lines.append(ln.strip())
        else:
            other_lines.append(ln.rstrip())

    list_lines.append(entry_line)

    # Deterministic unique + sorted by script key.
    uniq = {}
    for ln in list_lines:
        uniq[_key(ln)] = ln
    list_sorted = [uniq[k] for k in sorted(uniq.keys())]

    # Rebuild middle: keep any commentary lines first (stable), then the sorted list.
    rebuilt: list[str] = []
    for ln in other_lines:
        rebuilt.append(ln)
    for ln in list_sorted:
        rebuilt.append(ln)

    middle_out = "\n" + "\n".join(rebuilt) + "\n"

    out = before + BEGIN + middle_out + END + after
    REG.write_text(out, encoding="utf-8")

    print("OK: inserted autosync no-op proof into SV_PROOF_SURFACE_LIST block (style-aware, sorted).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
