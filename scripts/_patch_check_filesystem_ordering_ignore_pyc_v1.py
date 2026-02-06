from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

SENTINEL = "SV_PATCH: ignore python bytecode (__pycache__, *.pyc)"
INSERT = r"""# {sentinel}
# This gate scans repo files for nondeterministic filesystem-ordering patterns.
# Python bytecode (e.g., __pycache__/*.pyc) is NOT source-of-truth and can contain
# incidental string fragments that trip the scanner (e.g., "rglob(") even when
# the real source is correctly sorted().
#
# We exclude bytecode + __pycache__ to keep the gate focused on tracked text sources.
EXCLUDE_RE='(/__pycache__/|\.pyc$)'
# /{sentinel}
""".format(sentinel=SENTINEL)


def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if SENTINEL in txt:
        print("OK: target already excludes __pycache__/ and *.pyc")
        return

    # We patch by introducing EXCLUDE_RE and ensuring the scan pipeline applies it.
    # This patch is defensive: it only proceeds if we can find a reasonable anchor.
    anchors = [
        "=== Gate: Filesystem ordering determinism",
        "Filesystem ordering determinism gate",
    ]
    if not any(a in txt for a in anchors):
        die("refusing to patch: could not find expected anchor text in gate script")

    # Insert EXCLUDE_RE block after the initial banner/echo area (near the top).
    lines = txt.splitlines(True)
    out: list[str] = []
    inserted = False
    for i, ln in enumerate(lines):
        out.append(ln)
        # After first non-shebang non-empty line, drop in our block.
        if not inserted and i > 0 and ln.strip() != "" and not ln.startswith("#!/"):
            out.append("\n")
            out.append(INSERT)
            out.append("\n")
            inserted = True

    if not inserted:
        die("refusing to patch: could not find insertion point")

    new_txt = "".join(out)

    # Now ensure the scan stage filters out EXCLUDE_RE.
    # We handle two common patterns:
    #  1) find ... | ...
    #  2) git ls-files ... | ...
    #
    # We apply a minimal transform: pipe through grep -Ev "$EXCLUDE_RE" if not already present.
    if "EXCLUDE_RE" in new_txt and "grep -Ev \"${EXCLUDE_RE}\"" not in new_txt and "grep -Ev \"$EXCLUDE_RE\"" not in new_txt:
        # Try to locate a "files=" assignment or a pipeline that enumerates files.
        # We patch the first occurrence of a pipeline that looks like it enumerates files and is then scanned.
        repl_done = False
        patched_lines = []
        for ln in new_txt.splitlines(True):
            if (not repl_done) and ("git ls-files" in ln or "find " in ln) and ("| sort" in ln or "| grep" in ln or "| xargs" in ln):
                # If it's already filtering pyc, do nothing.
                if "__pycache__" in ln or ".pyc" in ln:
                    patched_lines.append(ln)
                    repl_done = True
                    continue
                # Add an exclude filter right after enumeration.
                if "| grep -Ev" in ln:
                    patched_lines.append(ln)
                    repl_done = True
                    continue
                # Heuristic: insert a grep -Ev "$EXCLUDE_RE" before the rest of the pipeline continues.
                parts = ln.split("|", 1)
                if len(parts) == 2:
                    head, tail = parts[0].rstrip(), parts[1]
                    ln2 = f"{head} | grep -Ev \"$EXCLUDE_RE\" |{tail}"
                    patched_lines.append(ln2)
                    repl_done = True
                    continue
            patched_lines.append(ln)

        if not repl_done:
            # Fallback: don't guess—make the exclusion explicit in a safe way by adding a note only.
            # (The earlier inserted block is still useful, but we'd prefer an actual filter.)
            die("refusing to patch: could not safely locate the file-enumeration pipeline to apply EXCLUDE_RE")

        new_txt = "".join(patched_lines)

    TARGET.write_text(new_txt, encoding="utf-8")
    print("OK: updated filesystem ordering determinism gate to ignore __pycache__/ and *.pyc")


if __name__ == "__main__":
    main()
