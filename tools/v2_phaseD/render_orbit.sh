#!/usr/bin/env bash
set -euo pipefail
: "${BASE:?signed Phase C .blend}" "${STUDIO:?signed scene renderer}"
D="${ORBIT_DIR:-/tmp/suzu_d/orbit}"
mkdir -p "$D"/{frames,logs,qc}
workers=()
for span in 1:90 91:180 181:270 271:360; do
 read -r a b <<< "${span/:/ }"
 (
  touch "$D/logs/chunk_${a}_${b}.started"
  if OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 blender -b "$BASE" -t 2 -P "$STUDIO" -- "$D/frames" orbit --start "$a" --end "$b" --samples 8 --movie-border 1152 > "$D/logs/chunk_${a}_${b}.log" 2>&1; then
   echo "$a $b" > "$D/logs/chunk_${a}_${b}.ok"
  else
   touch "$D/logs/chunk_${a}_${b}.failed";exit 1
  fi
 ) &
 workers+=("$!")
done
ok=0
for pid in "${workers[@]}"; do wait "$pid" || ok=1; done
exit "$ok"
