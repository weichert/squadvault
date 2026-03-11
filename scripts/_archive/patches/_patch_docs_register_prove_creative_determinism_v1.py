from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

# The new proof surface we must register (executed in prove_ci.sh)
ITEM = "scripts/prove_creative_determinism_v1.sh"

def insert_sorted_unique(lines: list[str], item: str) -> list[str]:
    item = item.rstrip("\n")
    stripped = [ln.rstrip("\n") for ln in lines]

    if item in stripped:
        return lines  # already present

    # Insert into a bullet list if present; otherwise insert as a plain list entry.
    # We support both "- path" and "• path" styles.
    # We'll preserve whatever style the neighboring list uses by inspecting candidates.
    # Find candidate list lines containing "scripts/prove_" or "scripts/gate_" etc.
    # Then insert lexicographically among similar script paths.
    script_idxs = []
    for i, ln in enumerate(stripped):
        core = ln.lstrip("-• ").strip()
        if core.startswith("scripts/") and ("/prove_" in core or core.startswith("scripts/prove_")):
            script_idxs.append(i)

    if not script_idxs:
        # Conservative fallback: append under a stable header if present
        return lines + [f"- {item}\n"]

    # Determine prefix style based on first script line
    first_ln = stripped[script_idxs[0]]
    prefix = "- "
    if first_ln.lstrip().startswith("•"):
        prefix = "• "

    # Build list of existing entries (core text) at those indices
    cores = []
    for i in script_idxs:
        core = stripped[i].lstrip("-• ").strip()
        cores.append((core, i))

    cores_sorted = sorted(cores, key=lambda t: t[0])

    # Find insertion position among cores_sorted
    insert_pos_line_idx = None
    for core, idx in cores_sorted:
        if item < core:
            insert_pos_line_idx = idx
            break

    if insert_pos_line_idx is None:
        # insert after the last script entry
        last_idx = max(script_idxs)
        out = lines[: last_idx + 1] + [f"{prefix}{item}\n"] + lines[last_idx + 1 :]
        return out

    out = lines[:insert_pos_line_idx] + [f"{prefix}{item}\n"] + lines[insert_pos_line_idx:]
    return out

def main() -> None:
    if not REG.exists():
        raise SystemExit(f"Missing registry doc: {REG}")

    txt = REG.read_text(encoding="utf-8")
    lines = txt.splitlines(keepends=True)

    new_lines = insert_sorted_unique(lines, ITEM)

    if new_lines == lines:
        return  # idempotent no-op

    REG.write_text("".join(new_lines), encoding="utf-8")

if __name__ == "__main__":
    main()
