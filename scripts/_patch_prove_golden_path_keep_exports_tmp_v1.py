from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    # Idempotency marker
    if "SV_PATCH_KEEP_EXPORT_TMP_V1" in s:
        print(f"OK: {TARGET} already patched (keep export tmp v1).")
        return

    # Heuristic: find a trap that cleans up the temp export dir.
    # We don't know exact variable name, so we patch in a safe conditional wrapper
    # right around the rm -rf that targets the golden path exports temp.
    lines = s.splitlines(True)

    # Try to locate the cleanup line that removes the golden path export temp dir.
    # Common patterns:
    #   rm -rf "$EXPORTS_TMP"
    #   rm -rf "${EXPORTS_TMP}"
    #   rm -rf "$TMP_EXPORTS_DIR"
    # We'll patch the first rm -rf line that mentions "sv_golden_path_exports" or "golden_path_exports"
    # OR any rm -rf inside a trap block after the mktemp for sv_golden_path_exports.
    idx_mk = None
    for i, line in enumerate(lines):
        if "sv_golden_path_exports" in line and ("mktemp" in line or "mktemp -d" in line):
            idx_mk = i
            break

    # Find cleanup rm -rf after mktemp, prefer within next ~120 lines
    rm_i = None
    search_start = idx_mk if idx_mk is not None else 0
    search_end = min(len(lines), search_start + 200)
    for i in range(search_start, search_end):
        if "rm -rf" in lines[i]:
            rm_i = i
            break

    if rm_i is None:
        raise SystemExit(
            "ERROR: could not locate cleanup 'rm -rf' after mktemp in scripts/prove_golden_path.sh.\n"
            "Open the file and search for the export temp dir mktemp + trap cleanup, then adjust patcher."
        )

    # Insert a guard around that rm -rf line
    orig = lines[rm_i]
    guard = (
        "# SV_PATCH_KEEP_EXPORT_TMP_V1\n"
        'if [[ "${SV_KEEP_EXPORT_TMP:-0}" == "1" ]]; then\n'
        '  echo "NOTE: SV_KEEP_EXPORT_TMP=1 — preserving golden path export temp dir"\n'
        "else\n"
        f"{orig.rstrip()}\n"
        "fi\n"
    )
    lines[rm_i] = guard

    # Also add a final note near where export paths are printed, if we can find "== Export assemblies =="
    injected = False
    for i, line in enumerate(lines):
        if line.strip() == 'echo "== Export assemblies =="':
            # insert after the block header
            lines.insert(
                i + 1,
                'echo "NOTE: set SV_KEEP_EXPORT_TMP=1 to preserve the temp export dir for inspection"\n',
            )
            injected = True
            break

    TARGET.write_text("".join(lines), encoding="utf-8")
    print(f"OK: patched {TARGET} (SV_KEEP_EXPORT_TMP keeps golden path export tmp dir).")

if __name__ == "__main__":
    main()
