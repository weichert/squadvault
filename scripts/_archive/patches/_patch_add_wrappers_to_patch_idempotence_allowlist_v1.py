from __future__ import annotations

from pathlib import Path

ALLOW = Path("scripts/patch_idempotence_allowlist_v1.txt")

WANT = [
    "scripts/patch_gate_ci_registry_execution_alignment_v1.sh",
    "scripts/patch_fix_ci_registry_execution_alignment_fail_v1.sh",
    "scripts/patch_gate_ci_registry_execution_alignment_exclude_prove_ci_v1.sh",
    "scripts/patch_registry_add_ci_execution_exempt_locals_v1.sh",
    "scripts/patch_index_ci_registry_execution_alignment_discoverability_v1.sh",
]


def is_entry_line(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    if s.startswith("#"):
        return False
    return True


def main() -> None:
    if not ALLOW.exists():
        raise SystemExit(f"ERROR: missing allowlist: {ALLOW}")

    # fail-closed: every wrapper must exist
    for p in WANT:
        if not Path(p).exists():
            raise SystemExit(f"ERROR: referenced wrapper missing: {p}")

    lines = ALLOW.read_text(encoding="utf-8").splitlines()
    header: list[str] = []
    entries: list[str] = []

    for ln in lines:
        if is_entry_line(ln):
            entries.append(ln.strip())
        else:
            header.append(ln.rstrip())

    merged = sorted(set(entries).union(set(WANT)))

    out = []
    out.extend(header)
    # ensure exactly one blank line between header and entries (canonical style)
    if out and out[-1].strip() != "":
        out.append("")
    out.extend(merged)
    out.append("")  # trailing newline

    ALLOW.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
