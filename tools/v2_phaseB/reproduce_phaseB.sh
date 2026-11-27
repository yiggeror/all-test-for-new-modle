#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
base=$(realpath "$1")
out=$(mkdir -p "$2" && realpath "$2")
work="$out/work"
mkdir -p "$work"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-"${TMPDIR:-/tmp}/suzu_blender_config"}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"${TMPDIR:-/tmp}/suzu_blender_cache"}
B=(blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1)
"${B[@]}" "$base" --python "$here/lock_snapshot.py" -- "$work/lock-before.json"
"${B[@]}" "$base" --python "$here/head/build_front.py" -- "$work/front"
"${B[@]}" --python "$here/head/build_back.py" -- "$work/back.blend"
"${B[@]}" "$work/front/front.blend" --python "$here/head/preview_phaseB.py" -- "$work/hair" fixture fixture-only back="$work/back.blend"
"${B[@]}" --python "$here/props/build_accessories.py" -- --output "$work/props.blend" --anchors "$here/props/mounts_45r2.json"
python3 "$here/paint/paint_hair.py" --out "$work/paint"
"${B[@]}" "$base" --python "$here/assemble_b.py" -- "$work/assembled.blend" --hair "$work/hair/head_fit.blend" --props "$work/props.blend"
"${B[@]}" "$work/assembled.blend" --python "$here/finish_look.py" -- "$here/paint" "$work/paint" "$work/painted.blend" --crown 1.562 --lower 1.124
"${B[@]}" "$work/painted.blend" --python "$here/lock_snapshot.py" -- "$work/lock-after.json"
cmp "$work/lock-before.json" "$work/lock-after.json"
"${B[@]}" "$work/painted.blend" --python "$here/studio_b.py" -- "$work/raw" --samples 40
python3 "$here/compose_b.py" "$work/raw" "$out/previews/v2_phaseB"
"${B[@]}" "$work/painted.blend" --python "$here/export_b.py" -- "$out/assets"
"${B[@]}" --python "$here/inspect_glb.py" -- "$out/assets/suzu_v2_phaseB.glb"
