from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

ADD = [
    "scripts/prove_local_clean_then_ci_v3.sh",
    "scripts/prove_local_shell_hygiene_v1.sh",
]

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing {DOC}")

    text = DOC.read_text(encoding="utf-8")

    # Fail-closed: require the doc already references at least one prove runner
    # (so we don't accidentally patch the wrong file).
    if "scripts/prove_" not in text:
        raise SystemExit(f"ERROR: {DOC} does not appear to be a proof registry (no scripts/prove_ references)")

    # Idempotent: only add entries not already present.
    missing = [p for p in ADD if p not in text]
    if not missing:
        return

    # Deterministic insertion:
    # append a small marker-bounded block at EOF listing these proofs explicitly.
    begin = "<!-- PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1_BEGIN -->"
    end = "<!-- PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1_END -->"

    if begin in text and end in text:
        # If marker block exists but missing some entries, replace block content deterministically.
        pre = text.split(begin)[0]
        post = text.split(end)[1]
        block_lines = [begin, "", "### Local hygiene proofs (registered)", ""]
        for p in sorted(set(ADD)):
            block_lines.append(f"- `{p}`")
        block_lines += ["", end, ""]
        DOC.write_text(pre.rstrip() + "\n\n" + "\n".join(block_lines) + post.lstrip(), encoding="utf-8")
        return

    block_lines = [begin, "", "### Local hygiene proofs (registered)", ""]
    for p in sorted(set(missing)):
        block_lines.append(f"- `{p}`")
    block_lines += ["", end, ""]
    patched = text.rstrip() + "\n\n" + "\n".join(block_lines) + "\n"
    DOC.write_text(patched, encoding="utf-8")

if __name__ == "__main__":
    main()
