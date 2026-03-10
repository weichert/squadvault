#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"

BLOCK_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
BLOCK_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BLOCK_PREFIX_LINES = [
    BLOCK_BEGIN,
    "# - Format: `- scripts/<path> — description`",
    "# - Only list gate/check entrypoints you intend to be validated as discoverable.",
    "# - This section is enforced by scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "# NOTE:",
    "## CI guardrails entrypoints (bounded)",
]

GATE_PATH_RE = re.compile(r"scripts/(gate_[A-Za-z0-9_]+\.sh)")

CANDIDATE_PATTERNS = (
    re.compile(r'(?:===|==>)\s*Gate:\s*(.+?)\s*(?:===)?\s*["\']?\s*$'),
    re.compile(r'\bGate:\s*(.+?)\s*(?:===)?\s*["\']?\s*$'),
    re.compile(r'(?:===|==>)\s*(.+?\bgate\b.*?)\s*(?:===)?\s*["\']?\s*$', re.IGNORECASE),
    re.compile(r'OK:\s*(.+?\bgate\b.*?)\s*["\']?\s*$', re.IGNORECASE),
)

LABEL_OVERRIDES = {
    "scripts/gate_ci_milestones_latest_block_v1.sh":
        "Enforce CI_MILESTONES.md has exactly one bounded ## Latest block (v1)",
}

TOKEN_OVERRIDES = {
    "ci": "CI",
    "cwd": "CWD",
    "toc": "TOC",
    "db": "DB",
    "pytest": "Pytest",
    "ops": "Ops",
    "bash": "Bash",
    "xtrace": "xtrace",
    "network": "network",
    "package": "package",
    "manager": "manager",
}

VERSION_SUFFIX_RE = re.compile(r"_v([0-9]+)$")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_ordered_gate_paths(prove_text: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    for raw_line in prove_text.splitlines():
        if re.match(r"^\s*#", raw_line):
            continue
        for match in GATE_PATH_RE.finditer(raw_line):
            rel_path = f"scripts/{match.group(1)}"
            if rel_path not in seen:
                seen.add(rel_path)
                ordered.append(rel_path)

    return ordered


def prettify_token(token: str) -> str:
    lower = token.lower()
    if lower in TOKEN_OVERRIDES:
        return TOKEN_OVERRIDES[lower]
    if token.isdigit():
        return token
    return token.capitalize()


def fallback_label_from_filename(rel_path: str) -> str:
    name = Path(rel_path).name
    stem = name[:-3] if name.endswith(".sh") else name
    if stem.startswith("gate_"):
        stem = stem[len("gate_"):]

    match = VERSION_SUFFIX_RE.search(stem)
    version = ""
    if match:
        version = f" (v{match.group(1)})"
        stem = stem[:match.start()]

    parts = [prettify_token(part) for part in stem.split("_") if part]
    label = normalize_space(" ".join(parts))
    if not label:
        raise RuntimeError(f"could not derive fallback label from: {rel_path}")
    return f"{label}{version}"


def derive_canonical_label(rel_path: str) -> str:
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
    return "\n".join(lines) + "\n"


def render_block_from_prove_path(prove_path: Path) -> str:
    if not prove_path.is_file():
        raise RuntimeError(f"missing prove script: {prove_path}")
    return render_block_from_prove_text(prove_path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prove", default=str(DEFAULT_PROVE))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prove_path = Path(args.prove)
    sys.stdout.write(render_block_from_prove_path(prove_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
