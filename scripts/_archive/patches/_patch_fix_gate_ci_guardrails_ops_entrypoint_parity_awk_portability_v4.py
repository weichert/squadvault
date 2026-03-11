from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

OLD = """awk -v b="${BEGIN}" -v e="${END}" '
  $0 ~ b {in=1; next}
  $0 ~ e {in=0}
  in {print}
' "${INDEX}" | awk '
  # match lines starting with "-" and containing scripts/...
  match($0, /^[[:space:]]*-[[:space:]]*(scripts\\/[^[:space:]]+)/, m) { print m[1] }
' | sed -e 's/[[:space:]]*$//' | sort -u > "${indexed_tmp}"
"""

NEW = """awk -v b="${BEGIN}" -v e="${END}" '
  $0 ~ b {inside=1; next}
  $0 ~ e {inside=0}
  inside {print}
' "${INDEX}" | awk '
  # Extract the first token starting with scripts/ from bullet lines.
  # Supports:
  #   - scripts/<path> — ...
  #   - scripts/<path> - ...
  #   - scripts/<path>
  /^[[:space:]]*-[[:space:]]*scripts\\// {
    line=$0
    sub(/^[[:space:]]*-[[:space:]]*/, "", line)
    sub(/[[:space:]].*$/, "", line)
    print line
  }
' | sed -e 's/[[:space:]]*$//' | sort -u > "${indexed_tmp}"
"""

def main() -> None:
    if not GATE.exists():
        raise SystemExit(f"ERROR: missing {GATE}")

    text = GATE.read_text(encoding="utf-8")

    if NEW in text:
        print("OK: gate already patched for awk portability (v4)")
        return

    if OLD not in text:
        raise SystemExit("ERROR: expected exact awk pipeline not found; refuse to patch")

    GATE.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print("UPDATED:", GATE)

if __name__ == "__main__":
    main()
