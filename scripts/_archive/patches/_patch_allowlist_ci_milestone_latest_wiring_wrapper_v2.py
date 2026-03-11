from __future__ import annotations

from pathlib import Path
import glob

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

WRAPPER = "scripts/patch_wire_ci_milestone_latest_into_append_wrapper_v1.sh"

# Use a known-allowlisted wrapper as a fingerprint to identify the correct allowlist file.
KNOWN_ALLOWLISTED = "scripts/patch_fix_ci_registry_execution_alignment_fail_v1.sh"

def _pick_allowlist() -> Path:
    # Prefer exact expected names if they exist (common variants).
    preferred = [
        SCRIPTS / "patch_wrapper_idempotence_allowlist_v1.txt",
        SCRIPTS / "patch_wrapper_idempotence_allowlist.txt",
        SCRIPTS / "patch_idempotence_allowlist_v1.txt",
        SCRIPTS / "patch_idempotence_allowlist.txt",
    ]
    for p in preferred:
        if p.exists():
            return p

    # Otherwise, search for plausible allowlist txt files.
    pats = [
        str(SCRIPTS / "*idempotence*allowlist*.txt"),
        str(SCRIPTS / "*allowlist*idempotence*.txt"),
        str(SCRIPTS / "*idempotent*allowlist*.txt"),
        str(SCRIPTS / "*allowlist*idempotent*.txt"),
    ]
    cands: list[Path] = []
    for pat in pats:
        for s in glob.glob(pat):
            p = Path(s)
            if p.exists() and p.is_file() and p not in cands:
                cands.append(p)

    if not cands:
        # Show operator-friendly hints without asking questions.
        txts = sorted(str(p.relative_to(ROOT)) for p in SCRIPTS.glob("*.txt"))
        raise SystemExit(
            "ERROR: could not find an idempotence allowlist under scripts/.\n"
            "HINT: expected something like '*idempotence*allowlist*.txt'.\n"
            f"Available scripts/*.txt:\n  " + "\n  ".join(txts)
        )

    # Pick the candidate that contains a known allowlisted wrapper.
    hits: list[Path] = []
    for p in cands:
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if KNOWN_ALLOWLISTED in s:
            hits.append(p)

    if len(hits) == 1:
        return hits[0]

    if len(hits) > 1:
        rel = "\n  ".join(str(p.relative_to(ROOT)) for p in hits)
        raise SystemExit(
            "ERROR: multiple candidate idempotence allowlists matched the fingerprint.\n"
            f"Matches:\n  {rel}\n"
            "Refuse to guess."
        )

    rel = "\n  ".join(str(p.relative_to(ROOT)) for p in cands)
    raise SystemExit(
        "ERROR: found candidate allowlist files but none contained the expected fingerprint entry.\n"
        f"Candidates:\n  {rel}\n"
        "Refuse to guess."
    )

def main() -> int:
    allow = _pick_allowlist()

    lines = allow.read_text(encoding="utf-8").splitlines()

    # Preserve only the leading header (comments/blank lines) verbatim.
    header: list[str] = []
    body: list[str] = []
    in_header = True
    for ln in lines:
        if in_header and (ln.strip() == "" or ln.lstrip().startswith("#")):
            header.append(ln)
            continue
        in_header = False
        body.append(ln)

    # Canonicalize body: keep only non-empty, non-comment entries; sort+unique; add our wrapper.
    entries = sorted({ln.strip() for ln in body if ln.strip() and not ln.lstrip().startswith("#")} | {WRAPPER})

    updated = "\n".join(header + entries) + "\n"
    cur = allow.read_text(encoding="utf-8")
    if updated == cur:
        print(f"OK: wrapper already allowlisted (noop): {allow}")
        return 0

    allow.write_text(updated, encoding="utf-8")
    print(f"OK: allowlisted CI milestone latest wiring wrapper in {allow}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
