#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

reassemble_one() {
  local name="$1"
  local expected_sha="$2"
  local out_file="$DIR/$name"
  shopt -s nullglob
  local parts=("$DIR/$name.part."*)
  shopt -u nullglob
  if [[ ${#parts[@]} -eq 0 ]]; then
    echo "Error: no chunk files found for $name in $DIR" >&2
    exit 1
  fi
  IFS=$'\n' read -r -d '' -a parts < <(printf '%s\n' "${parts[@]}" | sort && printf '\0')

  echo "Reassembling $name (${#parts[@]} chunks)..."
  cat "${parts[@]}" > "$out_file"

  if command -v sha256sum >/dev/null 2>&1; then
    local actual_sha
    actual_sha="$(sha256sum "$out_file" | awk '{print $1}')"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
      echo "SHA-256 mismatch for $name! Expected $expected_sha, got $actual_sha" >&2
      exit 1
    fi
    echo "OK: $out_file (SHA-256: $actual_sha)"
  elif command -v shasum >/dev/null 2>&1; then
    local actual_sha
    actual_sha="$(shasum -a 256 "$out_file" | awk '{print $1}')"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
      echo "SHA-256 mismatch for $name! Expected $expected_sha, got $actual_sha" >&2
      exit 1
    fi
    echo "OK: $out_file (SHA-256: $actual_sha)"
  else
    echo "Reassembled $out_file (sha256sum/shasum unavailable for verification)."
  fi
}

reassemble_one "monet_un_jour_a_giverny_1080p.mp4" "3aa53824aac32e28fad3bc1e34a896fdf8fd6d351176278dbddb9e7ac211bbba"
echo "Note: monet_un_jour_a_giverny_720p.mp4 is already stored directly as a single playable MP4."
