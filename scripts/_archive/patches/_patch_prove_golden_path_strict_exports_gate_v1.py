from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")

START_MARK = 'echo "== Export assemblies =="'
# Replace within the export block only:
REPL = '|| { rc=$?; if [[ "${SV_STRICT_EXPORTS:-0}" == "1" ]]; then exit $rc; fi; }'

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    # Find export block start
    start = None
    for i, line in enumerate(lines):
        if line.strip() == START_MARK:
            start = i
            break
    if start is None:
        raise SystemExit(f"ERROR: could not find export block start marker: {START_MARK!r}")

    # Find the next section header (next echo "== ... ==") after start
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].strip().startswith('echo "== ') and lines[j].strip().endswith(' =="') and lines[j].strip() != START_MARK:
            end = j
            break

    block = "".join(lines[start:end])

    # Idempotency
    if REPL in block:
        print("OK: export strict gate already present; no change.")
        return

    # Only patch if we actually see masking in the block
    if "|| true" not in block:
        raise SystemExit(
            "ERROR: did not find '|| true' inside the Export assemblies block. "
            "Refusing to patch blindly. (If exports are masked another way, we’ll patch that explicitly.)"
        )

    # Replace all occurrences of "|| true" within block
    new_block = block.replace("|| true", REPL)

    out = "".join(lines[:start]) + new_block + "".join(lines[end:])
    if out == s:
        raise SystemExit("ERROR: patch produced no changes (unexpected).")

    TARGET.write_text(out, encoding="utf-8")
    print(f"OK: patched {TARGET} (Export assemblies now strict when SV_STRICT_EXPORTS=1).")

if __name__ == "__main__":
    main()
