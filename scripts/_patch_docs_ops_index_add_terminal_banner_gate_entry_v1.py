from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_BEGIN -->"
END = "<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_END -->"

BLOCK = f"""{BEGIN}
## Terminal Banner Paste Gate (canonical)

- **Gate:** `scripts/gate_no_terminal_banner_paste_v1.sh`
- **Purpose:** Prevent pasted terminal/session banners (e.g., “Last login:”, zsh default shell banner) from entering tracked scripts/docs.
- **Escape hatch (emergency only):** `SV_ALLOW_TERMINAL_BANNER_PASTE=1`
  - Behavior: prints a clear `WARN`, skips enforcement, exits `0`.
  - Use: only to unblock urgent work; remove banner paste and re-run CI before merging.
- **Scan scope (fast + deterministic):** restricted to likely text files under `scripts/`:
  - `scripts/**/*.sh`
  - `scripts/**/*.py`
  - `scripts/**/*.md`
  - `scripts/**/*.txt`
- **Pattern discipline:** banner patterns are **anchored to start-of-line** (`^`) intentionally to avoid “self-matches”
  inside patchers/docs/gates (the gate should detect **pasted output**, not pattern literals embedded in source).

### Standard: text pathspecs for scan-based gates
When a gate scans `scripts/`, prefer a **pathspec allowlist** using git’s glob-magic pathspecs (avoid scanning unexpected types):

- `:(glob)scripts/**/*.sh`
- `:(glob)scripts/**/*.py`
- `:(glob)scripts/**/*.md`
- `:(glob)scripts/**/*.txt`

### Standard: “latest wrapper” convention
For a given patch family, treat the **highest version wrapper** as the canonical entrypoint:

- Example: `scripts/patch_*_v4.sh` supersedes `*_v3.sh`, etc.
- Older versions remain for auditability and historical provenance.

{END}
"""

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: expected ops index doc not found: {DOC}")

    text = DOC.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        print("OK: docs entry already present (idempotent).")
        return

    # Append at end with a separating blank line.
    if not text.endswith("\n"):
        text += "\n"
    if not text.endswith("\n\n"):
        text += "\n"

    DOC.write_text(text + BLOCK, encoding="utf-8")
    print(f"OK: appended terminal banner gate entry to {DOC}")

if __name__ == "__main__":
    main()
