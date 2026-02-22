from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"
INDEX_DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

GATE_SCRIPT = REPO_ROOT / "scripts" / "gate_creative_surface_registry_usage_v1.sh"
REGISTRY_DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "Creative_Surface_Registry_v1.0.md"
DISCOVERABILITY_GATE = REPO_ROOT / "scripts" / "gate_creative_surface_registry_discoverability_v1.sh"

BEGIN_INDEX = "<!-- SV_INDEX_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_BEGIN -->"
END_INDEX = "<!-- SV_INDEX_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_END -->"

BEGIN_PROVE = "<!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_BEGIN -->"
END_PROVE = "<!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_END -->"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, content: str) -> bool:
    existing = p.read_text(encoding="utf-8") if p.exists() else ""
    if existing == content:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return True


def _splice_marked_block(doc: str, begin: str, end: str, block: str) -> tuple[str, bool]:
    if begin in doc and end in doc:
        pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), flags=re.S)
        new = pattern.sub(block, doc, count=1)
        return new, (new != doc)
    new_doc = doc.rstrip() + "\n\n" + block + "\n"
    return new_doc, True


def _gate_script_text() -> str:
    # Quote-safe bash: avoid multiline "$(... \\" constructs.
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"',
        'cd "$repo_root"',
        "",
        "bash scripts/gate_creative_surface_registry_discoverability_v1.sh",
        "",
        'registry_doc="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"',
        'test -f "$registry_doc"',
        "",
        'registered_ids_raw="$(grep -h -o -E \'CREATIVE_SURFACE_[A-Z0-9_]+\' "$registry_doc" || true)"',
        'registered_ids="$(printf "%s\\n" "$registered_ids_raw" | sed \'/^$/d\' | sort -u)"',
        'if [ -z "$registered_ids" ]; then',
        '  echo "ERROR: no CREATIVE_SURFACE_* tokens found in registry doc" >&2',
        "  exit 1",
        "fi",
        "",
        'reg_total="$(printf "%s\\n" "$registered_ids_raw" | sed \'/^$/d\' | wc -l | tr -d \' \')"',
        'reg_unique="$(printf "%s\\n" "$registered_ids" | wc -l | tr -d \' \')"',
        'if [ "$reg_total" != "$reg_unique" ]; then',
        '  echo "ERROR: duplicate CREATIVE_SURFACE_* tokens in registry doc" >&2',
        "  exit 1",
        "fi",
        "",
        'usage_raw="$(git grep -h -o -E \'CREATIVE_SURFACE_[A-Z0-9_]+\' -- . '
        + "':!**/docs/80_indices/ops/Creative_Surface_Registry_v1.0.md' "
        + "':!**/artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json' "
        + "| sort -u || true)\"",
    ]
    # The line above is still risky due to embedded quotes; rebuild safely as separate lines.
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"',
        'cd "$repo_root"',
        "",
        "bash scripts/gate_creative_surface_registry_discoverability_v1.sh",
        "",
        'registry_doc="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"',
        'if [ ! -f "$registry_doc" ]; then',
        '  echo "ERROR: registry doc missing: $registry_doc" >&2',
        "  exit 1",
        "fi",
        "",
        'registered_ids_raw="$(grep -h -o -E \'CREATIVE_SURFACE_[A-Z0-9_]+\' "$registry_doc" || true)"',
        'registered_ids="$(printf "%s\\n" "$registered_ids_raw" | sed \'/^$/d\' | sort -u)"',
        'if [ -z "$registered_ids" ]; then',
        '  echo "ERROR: no CREATIVE_SURFACE_* tokens found in registry doc" >&2',
        "  exit 1",
        "fi",
        "",
        'reg_total="$(printf "%s\\n" "$registered_ids_raw" | sed \'/^$/d\' | wc -l | tr -d \' \')"',
        'reg_unique="$(printf "%s\\n" "$registered_ids" | wc -l | tr -d \' \')"',
        'if [ "$reg_total" != "$reg_unique" ]; then',
        '  echo "ERROR: duplicate CREATIVE_SURFACE_* tokens in registry doc" >&2',
        "  exit 1",
        "fi",
        "",
        "usage_raw=\"$(",
        "  git grep -h -o -E 'CREATIVE_SURFACE_[A-Z0-9_]+' -- . \\",
        "    ':!**/docs/80_indices/ops/Creative_Surface_Registry_v1.0.md' \\",
        "    ':!**/artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json' \\",
        "  | sort -u || true",
        ")\"",
        "",
        "# Filter out non-surface tokens (gate markers, script identifiers, registry meta)",
        "usage_ids=\"$(",
        '  printf "%s\\n" "$usage_raw" \\',
        "    | grep -v -E '(_BEGIN|_END)$' \\",
        "    | grep -v -E '_GATE_' \\",
        "    | grep -v -E 'CREATIVE_SURFACE_REGISTRY$' \\",
        "    | grep -v -E '_$' \\",
        "    | sed '/^$/d' \\",
        "    | sort -u || true",
        ")\"",
        "",
        'if [ -z "$usage_ids" ]; then',
        "  exit 0",
        "fi",
        "",
        "missing=\"$(",
        "  comm -23 \\",
        '    <(printf "%s\\n" "$usage_ids" | sort -u) \\',
        '    <(printf "%s\\n" "$registered_ids" | sort -u) || true',
        ")\"",
        "",
        'if [ -n "$missing" ]; then',
        '  echo "ERROR: Creative Surface IDs referenced but not registered in registry doc:" >&2',
        '  printf "%s\\n" "$missing" | sed \'s/^/ - /\' >&2',
        "  exit 1",
        "fi",
        "",
        "exit 0",
        "",
    ]
    return "\n".join(lines)


def _index_block() -> str:
    return "\n".join(
        [
            BEGIN_INDEX,
            "- **Gate: Creative Surface Registry Usage (v1)**  ",
            "  Ensures referenced Creative Surface IDs are present in `docs/80_indices/ops/Creative_Surface_Registry_v1.0.md` (canonical registry).  ",
            "  Run: `bash scripts/gate_creative_surface_registry_usage_v1.sh`",
            END_INDEX,
        ]
    )


def _prove_block() -> str:
    return "\n".join(
        [
            BEGIN_PROVE,
            'echo "=== Gate: Creative Surface registry usage (v1) ==="',
            "bash scripts/gate_creative_surface_registry_usage_v1.sh",
            END_PROVE,
        ]
    )


def main() -> None:
    changed = False

    if not PROVE_CI.exists():
        raise SystemExit("ERROR: scripts/prove_ci.sh missing")
    if not INDEX_DOC.exists():
        raise SystemExit("ERROR: docs/80_indices/ops/CI_Guardrails_Index_v1.0.md missing")
    if not REGISTRY_DOC.exists():
        raise SystemExit("ERROR: docs/80_indices/ops/Creative_Surface_Registry_v1.0.md missing")
    if not DISCOVERABILITY_GATE.exists():
        raise SystemExit("ERROR: scripts/gate_creative_surface_registry_discoverability_v1.sh missing")

    changed |= _write_if_changed(GATE_SCRIPT, _gate_script_text())

    idx = _read(INDEX_DOC)
    new_idx, did_idx = _splice_marked_block(idx, BEGIN_INDEX, END_INDEX, _index_block())
    if did_idx:
        changed |= _write_if_changed(INDEX_DOC, new_idx)

    prove = _read(PROVE_CI)
    new_prove, did_prove = _splice_marked_block(prove, BEGIN_PROVE, END_PROVE, _prove_block())
    if did_prove:
        changed |= _write_if_changed(PROVE_CI, new_prove)

    if not changed:
        print("NOOP: already canonical")


if __name__ == "__main__":
    main()
