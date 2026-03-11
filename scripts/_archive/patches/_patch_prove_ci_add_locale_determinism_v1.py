from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

BLOCK = """\
# ==> Determinism: pin locale + timezone (cross-runner stability)
# NOTE: Locale affects sort/collation, string casing, and some tooling output.
# Keep this pinned at the *authoritative* CI proof surface.
export TZ="${TZ:-UTC}"
export LC_ALL="${LC_ALL:-C}"
export LANG="${LANG:-C}"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if "Determinism: pin locale + timezone" in txt:
        print("OK: locale determinism block already present (no-op).")
        return

    lines = txt.splitlines(True)

    # Anchor strategy (prefer placing early, right after existing env envelope / strict mode)
    # We refuse if we can't find a safe, predictable insertion point.
    insert_after_idx: int | None = None

    # 1) After 'set -euo pipefail' (common & early)
    for i, ln in enumerate(lines):
        if ln.strip() == "set -euo pipefail":
            insert_after_idx = i
            break

    # 2) If no strict-mode line, try after a known env envelope marker if present
    if insert_after_idx is None:
        for i, ln in enumerate(lines):
            if "deterministic env envelope" in ln.lower():
                insert_after_idx = i
                break

    if insert_after_idx is None:
        raise SystemExit(
            "Refusing to patch: could not find a safe anchor (expected 'set -euo pipefail' "
            "or a deterministic env envelope marker) in scripts/prove_ci.sh"
        )

    # Insert with a blank line before/after to keep readability stable.
    insertion = "\n" + BLOCK + "\n"
    out = "".join(lines[: insert_after_idx + 1]) + insertion + "".join(lines[insert_after_idx + 1 :])

    TARGET.write_text(out, encoding="utf-8")
    print("OK: patched scripts/prove_ci.sh with locale/timezone determinism block.")

if __name__ == "__main__":
    main()
