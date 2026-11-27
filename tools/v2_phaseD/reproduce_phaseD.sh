#!/usr/bin/env bash
set -euo pipefail
tool=$(cd "$(dirname "$0")" && pwd)
repo=$(realpath "$tool/../..")
phase_c=$(realpath "$1")
out=$(mkdir -p "$2" && realpath "$2")
mkdir -p "$out/assets" "$out/previews/final" "$out/viewer"
cp -r "$repo/viewer/." "$out/viewer/"
cp "$repo/CREDITS.md" "$repo/start-viewer.cmd" "$out/"
cp "$phase_c/assets/suzu_v2_phaseC.blend" "$out/assets/suzu_final.blend"
cp "$phase_c/assets/suzu_v2_phaseC.glb" "$out/assets/suzu_final.glb"
python3 "$tool/package_viewer.py" "$out" "$out/suzu-viewer-offline.zip"
if [ "${3:-}" = "--viewer-only" ]; then exit 0; fi
cp "$phase_c/previews/v2_phaseC/motion_expression_showcase.mp4" "$out/previews/final/motion_final_1080p.mp4"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"${TMPDIR:-/tmp}/suzu_config"}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-"${TMPDIR:-/tmp}/suzu_config"}
export LP_NUM_THREADS=${LP_NUM_THREADS:-2}
blender -b "$out/assets/suzu_final.blend" -t "${SUZU_THREADS:-6}" --python-exit-code 1 -P "$tool/render_hero.py" -- "$out/previews/final/suzu_hero_render.png" --size 1800 2400 --samples 42
BASE="$out/assets/suzu_final.blend" STUDIO="$repo/tools/v2_phaseC/studio_c.py" ORBIT_DIR="$out/orbit-work" bash "$tool/render_orbit.sh"
python3 "$tool/pack_orbit.py" "$out/orbit-work/frames" "$out/previews/final/turntable_final_1080p.mp4"
python3 "$tool/verify_orbit.py" "$out/previews/final/turntable_final_1080p.mp4" --record "$out/orbit-work/verified.json"
