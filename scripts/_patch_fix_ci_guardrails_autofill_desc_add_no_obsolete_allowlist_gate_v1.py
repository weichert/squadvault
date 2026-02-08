from __future__ import annotations

from pathlib import Path

PATCHER = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

KEY = "scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh"
DESC_LINE = '    "scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh": "Reject obsolete allowlist rewrite recovery artifacts (v1)",\n'

def main() -> None:
    if not PATCHER.exists():
        raise SystemExit(f"ERROR: missing patcher file: {PATCHER}")

    src = PATCHER.read_text(encoding="utf-8")
    if KEY in src:
        print("OK: DESC already includes new gate path")
        return

    lines = src.splitlines(True)

    # Find the DESC map opening line: `DESC: dict[str, str] = {`
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("DESC:") and "{" in line:
            start = i
            break
    if start is None:
        raise SystemExit("ERROR: could not find DESC map start (refuse ambiguous edit)")

    # Find the closing brace of the DESC map by tracking brace depth from start
    depth = 0
    end = None
    for i in range(start, len(lines)):
        depth += lines[i].count("{")
        depth -= lines[i].count("}")
        if i > start and depth == 0:
            end = i
            break
    if end is None:
        raise SystemExit("ERROR: could not find DESC map end (refuse ambiguous edit)")

    # Insert just before the closing brace line
    lines.insert(end, DESC_LINE)
    PATCHER.write_text("".join(lines), encoding="utf-8")
    print(f"UPDATED: {PATCHER}")

if __name__ == "__main__":
    main()
