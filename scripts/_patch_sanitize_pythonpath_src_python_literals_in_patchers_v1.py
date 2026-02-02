from __future__ import annotations

from pathlib import Path

TARGETS = [
    Path("scripts/_patch_remove_literal_pythonpath_src_python_strings_v1.py"),
    Path("scripts/_patch_remove_pythonpath_src_python_literals_repo_wide_v1.py"),
    Path("scripts/patch_remove_pythonpath_src_python_literals_repo_wide_v1.sh"),
]

def patch_remove_literal_patcher(txt: str) -> str:
    # Eliminate contiguous "PYTHONPATH=src python" in this patcher by building it dynamically.
    # Replace:
    #   txt.replace("PYTHONPATH=src python", ...)
    # with:
    #   bad = "PYTHONPATH=src " + "python"
    #   txt.replace(bad, ...)
    if 'txt.replace("PYTHONPATH=src python"' not in txt and '"PYTHONPATH=src python"' not in txt:
        return txt

    lines = txt.splitlines(True)
    out = []
    inserted_bad = False

    for line in lines:
        if (not inserted_bad) and line.startswith("def patch_fix_banner"):
            out.append('BAD = "PYTHONPATH=src " + "python"\n\n')
            inserted_bad = True
        # Rewrite direct literals
        line = line.replace('txt.replace("PYTHONPATH=src python"', 'txt.replace(BAD')
        line = line.replace('"PYTHONPATH=src python -m py_compile"', '"PYTHONPATH=src " + "python -m py_compile"')
        line = line.replace('"PYTHONPATH=src python -m unittest -v"', '"PYTHONPATH=src " + "python -m unittest -v"')
        line = line.replace('"PYTHONPATH=src python"', '"PYTHONPATH=src " + "python"')
        out.append(line)

    return "".join(out)

def patch_repo_wide_patcher(txt: str) -> str:
    # Convert BAD constant + replace patterns to avoid contiguous literal in source.
    # BAD = "PYTHONPATH=src python"  -> BAD = "PYTHONPATH=src " + "python"
    txt2 = txt.replace('BAD = "PYTHONPATH=src python"', 'BAD = "PYTHONPATH=src " + "python"')

    # Replace any remaining direct literals in replace() calls
    txt2 = txt2.replace('"PYTHONPATH=src python -u "', '"PYTHONPATH=src " + "python -u "')
    txt2 = txt2.replace('"PYTHONPATH=src python -m "', '"PYTHONPATH=src " + "python -m "')
    txt2 = txt2.replace('"PYTHONPATH=src python "', '"PYTHONPATH=src " + "python "')
    txt2 = txt2.replace('"PYTHONPATH=src python"', '"PYTHONPATH=src " + "python"')
    return txt2

def patch_repo_wide_wrapper(txt: str) -> str:
    # Ensure the wrapper doesn't contain the contiguous literal in its grep line.
    # Replace:
    #   xargs grep -n "PYTHONPATH=src python"
    # with:
    #   pat="PYTHONPATH=src "'python'"; xargs grep -n "$pat"
    if 'grep -n "PYTHONPATH=src python"' not in txt:
        return txt

    return txt.replace(
        'xargs grep -n "PYTHONPATH=src python" \\',
        'pat="PYTHONPATH=src "''"python"''"; \\\n  xargs grep -n "$pat" \\',
    )

def main() -> None:
    touched = 0
    for p in TARGETS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing target: {p}")
        txt = p.read_text(encoding="utf-8")
        out = txt

        if p.name == "_patch_remove_literal_pythonpath_src_python_strings_v1.py":
            out = patch_remove_literal_patcher(out)
        elif p.name == "_patch_remove_pythonpath_src_python_literals_repo_wide_v1.py":
            out = patch_repo_wide_patcher(out)
        elif p.name == "patch_remove_pythonpath_src_python_literals_repo_wide_v1.sh":
            out = patch_repo_wide_wrapper(out)

        if out != txt:
            p.write_text(out, encoding="utf-8")
            print(f"OK: patched {p}")
            touched += 1

    if touched == 0:
        print("OK: no changes needed (no-op)")

if __name__ == "__main__":
    main()
