from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"

BEGIN = "<!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_BEGIN -->"
END = "<!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_END -->"

BEGIN_SAFE = "# " + BEGIN
END_SAFE = "# " + END


def main() -> None:
    if not PROVE_CI.exists():
        raise SystemExit("ERROR: scripts/prove_ci.sh missing")

    doc = PROVE_CI.read_text(encoding="utf-8")
    new = doc

    # Replace anywhere (embedded-safe). This is bash-correct because raw '<!--' is never valid bash.
    new = new.replace(BEGIN, BEGIN_SAFE)
    new = new.replace(END, END_SAFE)

    if new == doc:
        print("NOOP: already canonical")
        return

    PROVE_CI.write_text(new, encoding="utf-8")
    print("OK: normalized prove_ci HTML markers to bash comments (embedded-safe)")


if __name__ == "__main__":
    main()
