#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_FILE="${1:-${SCRIPT_DIR}/monet_un_jour_a_giverny_1080p.mp4}"
EXPECTED_SHA256="ca6f094658f4a07b0c2a76f9ce805d610d58ca39608f25d090b6a3589a5cf1da"

echo "Reassembling 1080p MP4 into: ${OUT_FILE}"
cat "${SCRIPT_DIR}/monet_un_jour_a_giverny_1080p.mp4.part.00" \
    "${SCRIPT_DIR}/monet_un_jour_a_giverny_1080p.mp4.part.01" > "${OUT_FILE}"

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL_SHA256="$(sha256sum "${OUT_FILE}" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  ACTUAL_SHA256="$(shasum -a 256 "${OUT_FILE}" | awk '{print $1}')"
else
  echo "Warning: sha256sum/shasum not found; skipping checksum verification."
  exit 0
fi

if [ "${ACTUAL_SHA256}" != "${EXPECTED_SHA256}" ]; then
  echo "ERROR: Checksum mismatch!"
  echo "  Expected: ${EXPECTED_SHA256}"
  echo "  Actual:   ${ACTUAL_SHA256}"
  exit 1
fi

echo "Verified SHA-256 (${ACTUAL_SHA256}): bit-exact lossless 1080p MP4 ready."
