#!/bin/bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
models=$(realpath "$1")
out=$(mkdir -p "$2" && realpath "$2")
mode=${3:-stills}
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-${TMPDIR:-/tmp}/suzu_blender_config}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-${TMPDIR:-/tmp}/suzu_blender_cache}
if [ "$mode" = "wip" ]; then
    blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1 --python "$here/gate1.py" -- "$models" "$out" wip
    python3 "$here/boards.py" "$out" "$out" wip
else
    frames="$out/raw"
    mkdir -p "$frames" "$out/previews/gate1"
    blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1 --python "$here/gate1.py" -- "$models" "$out" assets
    blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1 --python "$here/gate1.py" -- "$models" "$frames" stills
    g++ -std=c++17 -O3 "$here/edge_depth.cpp" -o "$frames/edge_depth"
    python3 "$here/composite_wire.py" "$frames/edge_depth" "$frames"
    python3 "$here/boards.py" "$frames" "$out/previews/gate1"
    if [ "$mode" != "stills" ]; then
        blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1 --python "$here/gate1.py" -- "$models" "$frames" motion
        ffmpeg -hide_banner -loglevel error -y -framerate 30 -start_number 1 -i "$frames/turn_%04d.png" -frames:v 210 -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -movflags +faststart "$out/previews/gate1/turntable_clay.mp4"
    fi
fi
