from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REG = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Proof_Surface_Registry_v1.0.md"

BEGIN = "<!-- SV_CI_EXECUTION_EXEMPT_v1_BEGIN -->"
END   = "<!-- SV_CI_EXECUTION_EXEMPT_v1_END -->"

ADD = "scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh\n"

def main() -> None:
    text = REG.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: expected SV_CI_EXECUTION_EXEMPT markers not found in registry; refusing to patch.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    # Canonicalize mid as: sorted unique non-empty lines, preserving leading/trailing blank lines.
    lines = mid.splitlines(keepends=True)

    prefix: list[str] = []
    suffix: list[str] = []

    i = 0
    while i < len(lines) and lines[i].strip() == "":
        prefix.append(lines[i])
        i += 1

    j = len(lines) - 1
    while j >= i and lines[j].strip() == "":
        suffix.append(lines[j])
        j -= 1
    suffix.reverse()

    entries: list[str] = []
    for ln in lines[i : j + 1]:
        if ln.strip() == "":
            continue
        entries.append(ln if ln.endswith("\n") else ln + "\n")

    s = set(entries)
    s.add(ADD)
    canon = sorted(s)

    new_mid = "".join(prefix) + "".join(canon) + "".join(suffix)
    REG.write_text(pre + BEGIN + new_mid + END + post, encoding="utf-8")

    print("OK: added to SV_CI_EXECUTION_EXEMPT block (sorted, unique).")

if __name__ == "__main__":
    main()
