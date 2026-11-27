#!/usr/bin/env bash
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
model=$(realpath "$1")
root=$(mkdir -p "$2" && realpath "$2")
shift 2
main="$root/frames"
mkdir -p "$main"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-"${TMPDIR:-/tmp}/suzu_config"}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"${TMPDIR:-/tmp}/suzu_cache"}
export LP_NUM_THREADS=2
if [ "$#" -eq 0 ]; then set -- '1:86' '87:172' '173:257' '258:342'; fi
pids=()
for range in "$@"; do
    IFS=: read -r lo hi <<<"$range"
    blender -b "$model" -t "${SUZU_JOB_THREADS:-2}" --python-exit-code 1 --python "$src/studio_c.py" -- "$main" motion --start "$lo" --end "$hi" --samples "${SUZU_MOTION_SAMPLES:-12}" --movie-border 1120 >"$root/motion-$lo-$hi.log" 2>&1 &
    pids+=("$!")
done
st=0
for pid in "${pids[@]}"; do wait "$pid" || st=1; done
test "$st" -eq 0
if [ "${SUZU_FRAMES_ONLY:-0}" != 1 ]; then
  python3 "$src/encode_movies.py" "$main" "$root/previews" motion
fi
