#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDERER = REPO_ROOT / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"
REGISTRY = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

REGISTRY_CONTENT = """scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh\tAllowlist patchers must insert sorted blocks (v1)
scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\tOps guardrails entrypoint block exactness gate (v1)
scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\tOps guardrails entrypoint parity gate (v1)
scripts/gate_ci_milestones_latest_block_v1.sh\tEnforce CI_MILESTONES.md has exactly one bounded ## Latest block (v1)
scripts/gate_creative_surface_registry_usage_v1.sh\tCreative surface registry usage gate (v1)
scripts/gate_docs_integrity_v2.sh\tDocs integrity gate (v2)
scripts/gate_no_network_in_ci_proofs_v1.sh\tNo network in CI proofs gate (v1)
scripts/gate_no_set_x_in_prove_and_gate_scripts_v1.sh\tNo forbidden set -x in prove/gate scripts (v1)
scripts/gate_ops_cwd_independence_v1.sh\tOps CWD independence gate (v1)
scripts/gate_ops_docs_no_orphaned_scripts_v1.sh\tOps docs no orphaned scripts gate (v1)
scripts/gate_ops_index_links_resolve_v1.sh\tOps index links resolve gate (v1)
scripts/gate_patch_wrapper_pairs_v1.sh\tPatch wrapper pairs gate (v1)
scripts/gate_prove_ci_references_existing_scripts_v1.sh\tprove_ci references existing scripts gate (v1)
scripts/gate_pytest_targets_are_tracked_v1.sh\tPytest targets are tracked gate (v1)
scripts/gate_worktree_cleanliness_v1.sh\tWorktree cleanliness gate (v1)
"""

OLD_DEFAULT_PROVE = 'DEFAULT_PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"\n'
NEW_DEFAULT_PROVE = '''DEFAULT_PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"
LABEL_REGISTRY_PATH = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
'''

INSERT_AFTER_VERSION_SUFFIX_RE = '''VERSION_SUFFIX_RE = re.compile(r"_v([0-9]+)$")
'''

HELPERS = '''

def load_label_registry(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(f"missing label registry: {path}")

    mapping: dict[str, str] = {}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "\\t" not in raw_line:
            raise RuntimeError(
                f"invalid label registry row at {path}:{lineno}: expected <path><TAB><label>"
            )
        rel_path, label = raw_line.split("\\t", 1)
        rel_path = normalize_space(rel_path)
        label = normalize_space(label)
        if not rel_path or not label:
            raise RuntimeError(
                f"invalid label registry row at {path}:{lineno}: empty path or label"
            )
        if rel_path in mapping and mapping[rel_path] != label:
            raise RuntimeError(
                f"duplicate label registry row for {rel_path} at {path}:{lineno}"
            )
        mapping[rel_path] = label

    return mapping


def extract_banner_label(rel_path: str) -> str | None:
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


def resolve_label(rel_path: str, registry: dict[str, str]) -> tuple[str | None, str]:
    if rel_path in registry:
        return registry[rel_path], "registry"
    if rel_path in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[rel_path], "override"

    banner_label = extract_banner_label(rel_path)
    if banner_label:
        return banner_label, "banner"

    return None, "missing"
'''

OLD_DERIVE = '''def derive_canonical_label(rel_path: str) -> str:
    if rel_path in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[rel_path]

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

    return fallback_label_from_filename(rel_path)


def render_block_from_prove_text(prove_text: str) -> str:
    gate_paths = extract_ordered_gate_paths(prove_text)
    bullets: list[str] = []

    for rel_path in gate_paths:
        label = derive_canonical_label(rel_path)
        bullets.append(f"- {rel_path} — {label}")

    lines = BLOCK_PREFIX_LINES + bullets + [BLOCK_END]
    return "\\n".join(lines) + "\\n"
'''

NEW_DERIVE = '''def render_block_from_prove_text(prove_text: str) -> str:
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

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"expected to find {label}")
    return text.replace(old, new, 1)

def main() -> int:
    if not RENDERER.is_file():
        raise RuntimeError(f"missing renderer: {RENDERER}")

    text = RENDERER.read_text(encoding="utf-8")
    original = text

    if 'LABEL_REGISTRY_PATH = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"' not in text:
        text = replace_once(text, OLD_DEFAULT_PROVE, NEW_DEFAULT_PROVE, "DEFAULT_PROVE block")

    if "def load_label_registry(path: Path) -> dict[str, str]:" not in text:
        anchor = INSERT_AFTER_VERSION_SUFFIX_RE
        if anchor not in text:
            raise RuntimeError("expected VERSION_SUFFIX_RE anchor")
        text = text.replace(anchor, anchor + HELPERS, 1)

    if "def derive_canonical_label(rel_path: str) -> str:" in text:
        text = replace_once(text, OLD_DERIVE, NEW_DERIVE, "derive/render block")
    elif "def resolve_label(rel_path: str, registry: dict[str, str]) -> tuple[str | None, str]:" not in text:
        raise RuntimeError("renderer is in unexpected state: missing derive_canonical_label / resolve_label")

    if text != original:
        RENDERER.write_text(text, encoding="utf-8")

    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    existing = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else None
    if existing != REGISTRY_CONTENT:
        REGISTRY.write_text(REGISTRY_CONTENT, encoding="utf-8")

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
