from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_remove_pythonpath_src_python_literals_repo_wide_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    # We want a safe, bash-valid pattern assignment that does NOT contain
    # the contiguous literal "PYTHONPATH=src python" in the file.
    # In bash, adjacent quoted strings concatenate:
    #   pat="PYTHONPATH=src ""python"
    # becomes: PYTHONPATH=src python at runtime (but not as a contiguous literal in source).
    #
    # Then use: xargs grep -n "$pat" \
    #
    # We'll replace any existing "pat=..." line plus the immediately following
    # grep invocation line if it matches our expected structure.

    lines = txt.splitlines(True)
    out: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]

        if line.lstrip().startswith("pat="):
            # Replace pat= line
            out.append('pat="PYTHONPATH=src ""python"\n')
            changed = True
            i += 1

            # If next non-empty line contains grep -n and "$pat", normalize it.
            if i < len(lines):
                nxt = lines[i]
                if "grep -n" in nxt and "$pat" in nxt:
                    out.append('  xargs grep -n "$pat" \\\n')
                    changed = True
                    i += 1
            continue

        out.append(line)
        i += 1

    if not changed:
        raise SystemExit("ERROR: did not find a pat= line to patch (refusing to guess)")

    TARGET.write_text("".join(out), encoding="utf-8")
    print(f"OK: patched {TARGET}")

if __name__ == "__main__":
    main()
