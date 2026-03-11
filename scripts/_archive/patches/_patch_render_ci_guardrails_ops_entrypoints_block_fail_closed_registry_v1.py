from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"

OLD = '''def render_block_from_prove_text(prove_text: str) -> str:
    gate_paths = extract_ordered_gate_paths(prove_text)
    registry = load_label_registry(LABEL_REGISTRY_PATH)
    bullets: list[str] = []
    missing: list[str] = []

    for rel_path in gate_paths:
        label, source = resolve_label(rel_path, registry)
        if source == "missing" or label is None:
            missing.append(rel_path)
            continue
        bullets.append(f"- {rel_path} — {label}")

    if missing:
        rendered = "\\n".join(f"- {path}" for path in missing)
        raise RuntimeError(
            "missing canonical CI guardrail labels for:\\n"
            f"{rendered}\\n"
            f"Add TSV entries to {LABEL_REGISTRY_PATH.relative_to(REPO_ROOT)} "
            "or add a clean self-describing banner."
        )

    lines = BLOCK_PREFIX_LINES + bullets + [BLOCK_END]
    return "\\n".join(lines) + "\\n"
'''

NEW = '''def render_block_from_prove_text(prove_text: str) -> str:
    gate_paths = extract_ordered_gate_paths(prove_text)
    registry = load_label_registry(LABEL_REGISTRY_PATH)
    bullets: list[str] = []
    missing: list[str] = []

    for rel_path in gate_paths:
        label = registry.get(rel_path)
        if label is None:
            missing.append(rel_path)
            continue
        bullets.append(f"- {rel_path} — {label}")

    if missing:
        rendered = "\\n".join(f"- {path}" for path in missing)
        raise RuntimeError(
            "missing canonical CI guardrail labels for:\\n"
            f"{rendered}\\n"
            f"Add TSV entries to {LABEL_REGISTRY_PATH.relative_to(REPO_ROOT)}."
        )

    lines = BLOCK_PREFIX_LINES + bullets + [BLOCK_END]
    return "\\n".join(lines) + "\\n"
'''

REMOVE_BLOCKS = (
'''LABEL_OVERRIDES = {
    "scripts/gate_ci_milestones_latest_block_v1.sh":
        "Enforce CI_MILESTONES.md has exactly one bounded ## Latest block (v1)",
}

''',
'''CANDIDATE_PATTERNS = (
    re.compile(r'(?:===|==>)\\s*Gate:\\s*(.+?)\\s*(?:===)?\\s*["\\']?\\s*$'),
    re.compile(r'\\bGate:\\s*(.+?)\\s*(?:===)?\\s*["\\']?\\s*$'),
    re.compile(r'(?:===|==>)\\s*(.+?\\bgate\\b.*?)\\s*(?:===)?\\s*["\\']?\\s*$', re.IGNORECASE),
    re.compile(r'OK:\\s*(.+?\\bgate\\b.*?)\\s*["\\']?\\s*$', re.IGNORECASE),
)

''',
'''def extract_banner_label(rel_path: str) -> str | None:
    gate_path = REPO_ROOT / rel_path
    if not gate_path.is_file():
        raise RuntimeError(f"missing gate script: {rel_path}")

    for raw_line in gate_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        for pattern in CANDIDATE_PATTERNS:
            match = pattern.search(stripped)
            if not match:
                continue
            label = normalize_space(match.group(1))
            if label:
                return label

    return None


''',
'''def resolve_label(rel_path: str, registry: dict[str, str]) -> tuple[str | None, str]:
    if rel_path in registry:
        return registry[rel_path], "registry"
    if rel_path in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[rel_path], "override"

    banner_label = extract_banner_label(rel_path)
    if banner_label:
        return banner_label, "banner"

    return None, "missing"


''',
)

def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)

def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if 'label = registry.get(rel_path)' in text and 'or add a clean self-describing banner.' not in text:
        print("OK: renderer already enforces registry-only bounded-block labels (noop)")
        return 0

    if OLD not in text:
        die("ERROR: expected render_block_from_prove_text block not found in renderer")

    text = text.replace(OLD, NEW, 1)

    for block in REMOVE_BLOCKS:
        if block in text:
            text = text.replace(block, "", 1)

    TARGET.write_text(text, encoding="utf-8")
    print("OK: patched renderer to enforce registry-only bounded-block label authority")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
