from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "logs" / "CI_MILESTONES.md"

BEGIN_LOG = "<!-- SV_CI_MILESTONE_LOG_v1_BEGIN -->"
END_LOG = "<!-- SV_CI_MILESTONE_LOG_v1_END -->"

BEGIN_LATEST = "<!-- SV_CI_MILESTONE_LATEST_v1_BEGIN -->"
END_LATEST = "<!-- SV_CI_MILESTONE_LATEST_v1_END -->"

def _extract_latest_entry(s: str) -> str:
    # First bullet inside the log block is the newest (you prepend).
    m = re.search(
        re.escape(BEGIN_LOG) + r"\s*\n(.*?)\n",
        s,
        flags=re.DOTALL,
    )
    if not m:
        raise SystemExit("ERROR: could not locate first entry inside milestone log block")
    line = m.group(1).rstrip()
    if not line.startswith("- "):
        raise SystemExit("ERROR: milestone entries must be markdown bullets starting with '- '")
    return line

def main() -> int:
    if not LOG.exists():
        raise SystemExit(f"ERROR: missing milestone log: {LOG}")

    s = LOG.read_text(encoding="utf-8")

    if BEGIN_LOG not in s or END_LOG not in s:
        raise SystemExit("ERROR: bounded log markers missing in CI_MILESTONES.md")

    latest = _extract_latest_entry(s)

    latest_block = (
        f"{BEGIN_LATEST}\n"
        f"**Latest:** {latest[2:]}\n"
        f"{END_LATEST}\n"
    )

    if BEGIN_LATEST in s and END_LATEST in s:
        # Replace existing latest block contents.
        updated = re.sub(
            re.escape(BEGIN_LATEST) + r".*?" + re.escape(END_LATEST) + r"\n?",
            latest_block,
            s,
            flags=re.DOTALL,
        )
        if updated == s:
            print("OK: latest section already canonical (noop).")
            return 0
        LOG.write_text(updated, encoding="utf-8")
        print("OK: updated latest milestone section.")
        return 0

    # Insert Latest block right under the title line.
    # Expect file starts with "# CI Milestones"
    if not s.lstrip().startswith("# CI Milestones"):
        raise SystemExit("ERROR: unexpected CI_MILESTONES.md header; expected '# CI Milestones'")

    # Insert after first blank line following the header.
    # Find header line end, then first double-newline boundary.
    hdr_end = s.find("\n")
    if hdr_end == -1:
        raise SystemExit("ERROR: malformed CI_MILESTONES.md (no newline)")

    # Place after header + one blank line.
    insert_at = hdr_end + 1
    if s[insert_at:insert_at+1] != "\n":
        # Ensure one blank line after header
        prefix = s[:insert_at] + "\n"
        rest = s[insert_at:]
        s = prefix + rest
        insert_at = hdr_end + 2

    updated = s[:insert_at] + latest_block + "\n" + s[insert_at:]
    LOG.write_text(updated, encoding="utf-8")
    print("OK: inserted latest milestone section.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
