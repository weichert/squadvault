from __future__ import annotations

from pathlib import Path
import sys

GATE = Path("scripts/gate_no_terminal_banner_paste_v1.sh")

def main() -> int:
    if not GATE.exists():
        raise SystemExit(f"REFUSE: missing gate: {GATE}")

    text = GATE.read_text(encoding="utf-8")

    # Replace the fragile xargs pipeline with safe git-grep over scripts/
    if "xargs: command line cannot be assembled" in text:
        # (should never be in file; defensive)
        pass

    # Minimal, surgical rewrite: replace the scanning loop body
    old_marker = "# Grep all tracked text-like files under scripts/. Avoid __pycache__."
    if old_marker not in text:
        raise SystemExit(f"REFUSE: expected marker not found in gate: {old_marker}")

    # New implementation uses git grep on tracked files within scripts/
    new_block = """# Grep tracked files under scripts/ (safe: no xargs arg explosion).
hits=0
for pat in "${patterns[@]}"; do
  # git grep returns 1 if no matches; treat that as OK.
  out="$(git grep -nE "${pat}" -- 'scripts/*' 2>/dev/null || true)"
  if [[ -n "${out}" ]]; then
    echo "ERROR: found pasted terminal banner lines matching: ${pat}" >&2
    echo "${out}" >&2
    hits=1
  fi
done
"""

    # Find and replace the entire old scanning section from marker through the loop end.
    # We’ll replace between the marker line and the line just before:
    # 'if [[ "${hits}" -ne 0 ]]; then'
    start = text.find(old_marker)
    end_anchor = 'if [[ "${hits}" -ne 0 ]]; then'
    end = text.find(end_anchor)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("REFUSE: could not locate scan block to replace")

    # Keep the marker line itself, then insert new_block, then keep the remainder from end_anchor onward.
    prefix = text[:start] + old_marker + "\n"
    suffix = text[end:]
    new_text = prefix + new_block + "\n" + suffix

    if new_text != text:
        GATE.write_text(new_text, encoding="utf-8")

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
