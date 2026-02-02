from __future__ import annotations

from pathlib import Path

STATUS_FILE_REL = "scripts/_status.sh"

STATUS_SH = """#!/usr/bin/env bash
# SquadVault — Shared Status Helpers
# Purpose: Consistent, human-readable status output across scripts
# Scope: Bash-only, no side effects, safe to source multiple times

# Ensure UTF-8 (best-effort, non-fatal)
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

# Symbols
SV_OK="✅"
SV_FAIL="❌"
SV_WARN="⚠️"
SV_INFO="ℹ️"
SV_SKIP="⏭️"

# Formatting helpers
sv_ok()    { echo "${SV_OK} $*"; }
sv_fail()  { echo "${SV_FAIL} $*" >&2; }
sv_warn()  { echo "${SV_WARN} $*"; }
sv_info()  { echo "${SV_INFO} $*"; }
sv_skip()  { echo "${SV_SKIP} $*"; }

# Structured status line (scan-friendly)
# Usage: sv_status "Wk 7" PASS
sv_status() {
  local label="$1"
  local status="$2"

  case "$status" in
    PASS) echo "$label   ${SV_OK} PASS" ;;
    FAIL) echo "$label   ${SV_FAIL} FAIL" ;;
    WARN) echo "$label   ${SV_WARN} WARN" ;;
    SKIP) echo "$label   ${SV_SKIP} SKIPPED" ;;
    *)    echo "$label   ${SV_INFO} $status" ;;
  esac
}
"""

# Block to insert into scripts
SOURCE_BLOCK = """\
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_status.sh"
"""

def is_shell_script(path: Path) -> bool:
    if path.suffix in {".sh", ".bash"}:
        return True
    # Heuristic: scripts without suffix but with shebang
    try:
        head = path.read_text(encoding="utf-8").splitlines()[:1]
    except Exception:
        return False
    return bool(head) and head[0].startswith("#!") and "bash" in head[0]

def already_sources_status(text: str) -> bool:
    return "_status.sh" in text and "source" in text

def insert_after_preamble(lines: list[str]) -> list[str]:
    """
    Insert the SOURCE_BLOCK after:
      - shebang line (if present)
      - and immediately after a 'set -euo pipefail' line if it exists near top
    We keep the insertion near the top for predictable behavior.
    """
    if not lines:
        return lines

    insert_at = 0

    # If shebang exists, insert after it
    if lines[0].startswith("#!"):
        insert_at = 1

    # If next few lines contain set -euo pipefail, insert after it
    for i in range(insert_at, min(insert_at + 8, len(lines))):
        if lines[i].strip() == "set -euo pipefail":
            insert_at = i + 1
            break

    # Avoid double blank lines
    block_lines = SOURCE_BLOCK.splitlines()
    out = lines[:insert_at] + [""] + block_lines + [""] + lines[insert_at:]
    return out

def main() -> int:
    repo_root = Path(".").resolve()
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.exists():
        print("ERROR: scripts/ directory not found.")
        return 2

    # 1) Ensure scripts/_status.sh exists
    status_path = repo_root / STATUS_FILE_REL
    if not status_path.exists():
        status_path.write_text(STATUS_SH, encoding="utf-8")
        print(f"CREATE {STATUS_FILE_REL}")
    else:
        # If exists but empty, restore canonical content
        existing = status_path.read_text(encoding="utf-8")
        if len(existing.strip()) == 0:
            status_path.write_text(STATUS_SH, encoding="utf-8")
            print(f"REWRITE {STATUS_FILE_REL} (was empty)")
        else:
            print(f"KEEP   {STATUS_FILE_REL}")

    # 2) Patch scripts
    changed = 0
    skipped = 0

    for path in sorted(scripts_dir.iterdir()):
        if path.name == "_status.sh":
            continue
        if path.name.startswith("_patch_"):
            continue
        if path.is_dir():
            continue
        if not is_shell_script(path):
            continue

        text = path.read_text(encoding="utf-8")
        if already_sources_status(text):
            skipped += 1
            continue

        lines = text.splitlines()
        new_lines = insert_after_preamble(lines)
        new_text = "\n".join(new_lines).rstrip() + "\n"

        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"PATCH  scripts/{path.name}")

    print(f"\nDone. patched={changed} skipped={skipped}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
