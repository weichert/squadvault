#!/usr/bin/env bash
set -euo pipefail

NOTE_PATH="docs/addenda/EAL_v1_Writer_Consumption_Boundary_Freeze.md"
TAG="eal-v1-writer-boundary"

echo "=== Docs freeze: EAL v1 writer consumption boundary ==="

if [[ ! -f "$NOTE_PATH" ]]; then
  echo "ERROR: expected note missing: $NOTE_PATH"
  echo "Create it first (see chat instructions)."
  exit 1
fi

# --- Patch Documentation Map (markdown) if present ---
DOCMAP="$(ls docs/*Documentation*Map*.md 2>/dev/null | head -n 1 || true)"
if [[ -n "${DOCMAP}" ]]; then
  echo "Found Documentation Map (md): $DOCMAP"
  if ! grep -q "EAL v1 writer consumption boundary" "$DOCMAP"; then
    cat >> "$DOCMAP" <<EOF2

## Addenda — Editorial Attunement Layer (EAL)

- **EAL v1 — Writer Consumption Boundary (Frozen)** — see \`$NOTE_PATH\` (tag: \`$TAG\`)
  - Read-only directives consumption; no impact on selection/ordering/facts/window
  - Guardrail: \`Tests/test_eal_writer_boundary_v1.py\`
EOF2
    echo "OK: appended EAL entry to Documentation Map"
  else
    echo "OK: Documentation Map already references EAL v1 boundary"
  fi
else
  echo "NOTE: No Documentation Map markdown found under docs/. (DOCX/PDF may exist.)"
  echo "      Manual: add a one-line cross-ref to $NOTE_PATH (tag: $TAG)."
fi

# --- Patch Core Engine spec (markdown) if present ---
CORESPEC="$(ls docs/*Core*Engine*Spec*.md 2>/dev/null | head -n 1 || true)"
if [[ -n "${CORESPEC}" ]]; then
  echo "Found Core Engine spec (md): $CORESPEC"
  if ! grep -q "eal-v1-writer-boundary" "$CORESPEC"; then
    cat >> "$CORESPEC" <<EOF3

## Editorial Attunement Layer (EAL) — Frozen Boundary (v1)

EAL v1 is integrated as a **writer-only, read-only** consumption boundary and is **frozen**
(tag: \`$TAG\`). It must not influence selection, ordering, canonical facts, or window bounds.
See: \`$NOTE_PATH\`.
EOF3
    echo "OK: appended EAL cross-reference to Core Engine spec"
  else
    echo "OK: Core Engine spec already references EAL v1 boundary"
  fi
else
  echo "NOTE: No Core Engine spec markdown found under docs/. (DOCX/PDF may exist.)"
  echo "      Manual: add a one-paragraph cross-ref pointing to $NOTE_PATH (tag: $TAG)."
fi

echo "DONE: docs freeze patch complete"
