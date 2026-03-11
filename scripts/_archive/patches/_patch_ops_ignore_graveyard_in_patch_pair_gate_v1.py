from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_patch_pairs_v1.sh")

ANCHOR_1 = "git ls-files 'scripts/patch_*.sh'"
ANCHOR_2 = "git ls-files 'scripts/_patch_*.py'"

def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")

    if "scripts/_graveyard/" in raw and "PATCH_PAIR_IGNORE_PREFIX" in raw:
        print("OK: graveyard ignore already present")
        return 0

    if ANCHOR_1 not in raw or ANCHOR_2 not in raw:
        raise RuntimeError(
            "Could not find expected anchors in scripts/check_patch_pairs_v1.sh.\n"
            f"Missing: {ANCHOR_1!r} or {ANCHOR_2!r}\n"
            "Run:\n"
            "  grep -n \"git ls-files 'scripts/patch_\\*.sh'\" scripts/check_patch_pairs_v1.sh\n"
            "  grep -n \"git ls-files 'scripts/_patch_\\*.py'\" scripts/check_patch_pairs_v1.sh\n"
        )

    lines = raw.splitlines(keepends=True)
    out: list[str] = []
    inserted_config = False

    # Insert config block near the top, after the initial header/vars.
    # We key off the ALLOWLIST= line if present; otherwise after the first 20 lines.
    insert_after_idx = None
    for i, line in enumerate(lines):
        if line.startswith("ALLOWLIST=") or line.startswith("ALLOWLIST =") or "ALLOWLIST=" in line:
            insert_after_idx = i
            break
    if insert_after_idx is None:
        insert_after_idx = min(20, len(lines) - 1)

    for i, line in enumerate(lines):
        out.append(line)
        if (not inserted_config) and i == insert_after_idx:
            out.append("\n")
            out.append("# Patch-pairing gate: ignore archive paths (v1)\n")
            out.append('PATCH_PAIR_IGNORE_PREFIX="scripts/_graveyard/"\n')
            out.append("\n")
            inserted_config = True

    raw2 = "".join(out)

    # Rewrite the two file-list commands to exclude scripts/_graveyard/
    # We keep it Bash 3.2 safe: use grep -v with a fixed prefix.
    raw2 = raw2.replace(
        "git ls-files 'scripts/patch_*.sh'",
        "git ls-files 'scripts/patch_*.sh' | grep -v \"^${PATCH_PAIR_IGNORE_PREFIX}\"",
        1,
    )
    raw2 = raw2.replace(
        "git ls-files 'scripts/_patch_*.py'",
        "git ls-files 'scripts/_patch_*.py' | grep -v \"^${PATCH_PAIR_IGNORE_PREFIX}\"",
        1,
    )

    TARGET.write_text(raw2, encoding="utf-8")
    print("OK: pairing gate now ignores scripts/_graveyard/** (v1)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
