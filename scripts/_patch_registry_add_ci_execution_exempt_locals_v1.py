from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CI_EXECUTION_EXEMPT_v1_BEGIN -->"
END = "<!-- SV_CI_EXECUTION_EXEMPT_v1_END -->"

WANT = [
    "scripts/prove_local_clean_then_ci_v3.sh # local-only: developer workflow proof (not executed in CI)",
    "scripts/prove_local_shell_hygiene_v1.sh # local-only: interactive shell hygiene proof (not executed in CI)",
]


def norm(s: str) -> str:
    return " ".join(s.strip().split())


def main() -> None:
    if not REG.exists():
        raise SystemExit(f"ERROR: missing {REG}")

    text = REG.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        mid, post = rest.split(END, 1)

        existing = [ln.rstrip("\n") for ln in mid.splitlines()]
        seen = {norm(ln) for ln in existing if norm(ln)}

        for w in WANT:
            if norm(w) not in seen:
                existing.append(w)

        uniq: dict[str, str] = {}
        for ln in existing:
            n = norm(ln)
            if not n:
                continue
            uniq[n] = ln.strip()

        sorted_lines = sorted(uniq.values(), key=lambda x: x.split()[0])
        new_mid = "\n".join([""] + sorted_lines + [""])

        REG.write_text(pre + BEGIN + new_mid + END + post, encoding="utf-8")
        return

    block = "\n".join(
        [
            "",
            BEGIN,
            "",
            *sorted(WANT, key=lambda x: x.split()[0]),
            "",
            END,
            "",
        ]
    )
    REG.write_text(text.rstrip() + block, encoding="utf-8")


if __name__ == "__main__":
    main()
