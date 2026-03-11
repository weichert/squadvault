from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")
SENTINEL = "SV_PATCH: fs-order scan ignore __pycache__/ and *.pyc (v2)"

# We will harden any grep invocation used for scanning by:
# - ignoring binary files: -I  (portable)
# - excluding __pycache__ dirs
# - excluding *.pyc files
#
# We do NOT assume how files are enumerated.

GREP_HARDEN = r'-I --exclude-dir=__pycache__ --exclude=*.pyc'

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if SENTINEL in txt:
        print("OK: gate already hardened for pyc/__pycache__")
        return

    # Insert a short comment block near the top (after shebang).
    lines = txt.splitlines(True)
    out = []
    inserted = False
    for i, ln in enumerate(lines):
        out.append(ln)
        if not inserted and i == 0 and ln.startswith("#!"):
            out.append("\n")
            out.append(f"# {SENTINEL}\n")
            out.append("# NOTE: wrappers run py_compile; __pycache__/*.pyc can contain incidental strings\n")
            out.append("# that trip this static scanner. Exclude bytecode + ignore binary files.\n")
            out.append("# /SV_PATCH\n\n")
            inserted = True

    txt2 = "".join(out)

    # Harden grep calls used for scanning (very common pattern).
    # We only patch grep invocations that already look like repo scans:
    # grep -R / grep -r / grep -RIn / grep -rInE etc.
    #
    # We avoid patching:
    #   - grep used for tiny single-file checks
    #   - grep -E on literal strings without -R/-r
    #
    # Heuristic: patch lines containing "grep" AND ("-R" or "-r") AND not already excluding pyc.
    changed = 0
    patched_lines = []
    for ln in txt2.splitlines(True):
        if ("grep" in ln) and ((" -R" in ln) or (" -r" in ln) or ln.strip().startswith("grep -R") or ln.strip().startswith("grep -r")):
            if "__pycache__" in ln or "*.pyc" in ln or "--exclude-dir=__pycache__" in ln or "--exclude=*.pyc" in ln or " -I " in ln:
                patched_lines.append(ln)
                continue

            # Insert hardening flags right after "grep"
            # Examples:
            #   grep -RInE 'pat' .
            #   grep -R 'pat' "$ROOT"
            parts = ln.split("grep", 1)
            if len(parts) == 2:
                prefix, rest = parts[0], parts[1]
                ln = f"{prefix}grep {GREP_HARDEN}{rest}"
                changed += 1

        patched_lines.append(ln)

    if changed == 0:
        die(
            "refusing to patch: did not find any recursive grep (-R/-r) lines to harden. "
            "Paste the gate script and we’ll patch the exact scan path."
        )

    TARGET.write_text("".join(patched_lines), encoding="utf-8")
    print(f"OK: hardened filesystem ordering gate: patched {changed} recursive grep line(s)")

if __name__ == "__main__":
    main()
