#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts.create_recap_artifact_draft_idempotent accepts artifact_type ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_recap_artifacts_create_draft_accept_artifact_type_v1.py

echo "OK: patch applied."
