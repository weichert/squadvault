#!/usr/bin/env bash
set -euo pipefail

log() { printf '%s\n' "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

# ---- inputs (override via env) ----
SRC="${SRC:-}"
BATCH_DIR="${BATCH_DIR:-docs/_import/VENDOR/2026-01-28_batch3}"
STAGE_DIR="${STAGE_DIR:-/tmp/squadvault_docs_import/2026-01-28_batch3}"

[ -n "${SRC}" ] || die "SRC is empty. Run with SRC=... set."
[ -f "${SRC}" ] || die "Source file not found: ${SRC}"

# Resolve repo root from this script location (CWD-independent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Sanity: non-zero file size
SRC_SIZE="$(/usr/bin/stat -f%z "${SRC}" 2>/dev/null || true)"
[ -n "${SRC_SIZE}" ] || die "Unable to stat source file: ${SRC}"
[ "${SRC_SIZE}" -gt 0 ] || die "Source file is 0 bytes: ${SRC}"

# Best-effort iCloud download request (fail-loud if brctl errors)
if command -v brctl >/dev/null 2>&1; then
  log "iCloud: requesting download via brctl..."
  brctl download "${SRC}" || die "brctl download failed for: ${SRC}"
fi

# Stage to /tmp using plain read/write (avoids openrsync mmap timeouts)
mkdir -p "${STAGE_DIR}"
STAGED_BASENAME="$(/usr/bin/basename "${SRC}")"
STAGED_PATH="${STAGE_DIR}/${STAGED_BASENAME}"

log "==> stage: SRC -> /tmp (cat; no mmap)"
if [ -f "${STAGED_PATH}" ]; then
  STAGED_SIZE="$(/usr/bin/stat -f%z "${STAGED_PATH}" 2>/dev/null || true)"
  if [ -n "${STAGED_SIZE}" ] && [ "${STAGED_SIZE}" = "${SRC_SIZE}" ] && [ "${STAGED_SIZE}" -gt 0 ]; then
    log "OK: /tmp staged file already present with matching size; skipping rewrite."
  else
    rm -f "${STAGED_PATH}.tmp"
    /bin/cat "${SRC}" > "${STAGED_PATH}.tmp" || die "cat failed reading iCloud file (not locally readable): ${SRC}"
    /bin/mv -f "${STAGED_PATH}.tmp" "${STAGED_PATH}"
  fi
else
  rm -f "${STAGED_PATH}.tmp"
  /bin/cat "${SRC}" > "${STAGED_PATH}.tmp" || die "cat failed reading iCloud file (not locally readable): ${SRC}"
  /bin/mv -f "${STAGED_PATH}.tmp" "${STAGED_PATH}"
fi

# Verify staged file
STAGED_SIZE2="$(/usr/bin/stat -f%z "${STAGED_PATH}" 2>/dev/null || true)"
[ -n "${STAGED_SIZE2}" ] || die "Unable to stat staged file: ${STAGED_PATH}"
[ "${STAGED_SIZE2}" -gt 0 ] || die "Staged file is 0 bytes: ${STAGED_PATH}"

# Copy into vendor batch dir via rsync (local -> local; idempotent)
mkdir -p "${BATCH_DIR}"
DEST_PATH="${BATCH_DIR}/${STAGED_BASENAME}"

log "==> rsync: /tmp stage -> vendor batch dir"
# --checksum for idempotence even if timestamps differ
/usr/bin/rsync -a --checksum --partial "${STAGED_PATH}" "${DEST_PATH}" \
  || die "rsync failed copying staged file into vendor dir: ${DEST_PATH}"

DEST_SIZE="$(/usr/bin/stat -f%z "${DEST_PATH}" 2>/dev/null || true)"
[ -n "${DEST_SIZE}" ] || die "Unable to stat vendor file: ${DEST_PATH}"
[ "${DEST_SIZE}" -gt 0 ] || die "Vendor file is 0 bytes after copy: ${DEST_PATH}"

log "OK: staged vendor file: ${DEST_PATH} (${DEST_SIZE} bytes)"
