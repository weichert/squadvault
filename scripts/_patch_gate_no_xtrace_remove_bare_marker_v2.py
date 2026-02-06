from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_no_xtrace_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    # Replace the heredoc line that starts with a bare marker.
    needle = "\n==> remediation\n"
    if needle not in txt:
        print("OK: no bare '==> remediation' line found (no-op).")
        return

    out = txt.replace(needle, "\nRemediation:\n", 1)
    TARGET.write_text(out, encoding="utf-8")
    print("OK: replaced bare '==> remediation' with 'Remediation:' in gate_no_xtrace_v1.sh")

if __name__ == "__main__":
    main()
