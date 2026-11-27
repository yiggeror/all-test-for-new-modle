#!/usr/bin/env bash
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
base=$(realpath "$1")
q=$(mkdir -p "$2" && realpath "$2")
mkdir -p "$q/impl" "$q/work" "$q/raw"
cp -r "$src/." "$q/impl/"
d="$q/impl"
w="$q/work"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-"${TMPDIR:-/tmp}/suzu_config"}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"${TMPDIR:-/tmp}/suzu_cache"}
B=(blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1)
"${B[@]}" "$base" --python "$d/hair/prepare_hair.py" -- "$w/hair_static.blend"
TOP_OUT="$w/top_tryon.blend" "${B[@]}" "$base" --python "$d/top/build_top.py"
TOP_NO_MODIFIER=1 TOP_BOUND="$w/top_module.blend" "${B[@]}" "$w/top_tryon.blend" --python "$d/top/bind_top.py"
JEWELRY_OUT="$w" JEWELRY_TAG=_R55 "${B[@]}" "$w/top_tryon.blend" --python "$d/top/jewelry/fit.py"
"${B[@]}" "$base" --python "$d/lower/build_lower.py" -- --out "$w/lower_fit.blend"
"${B[@]}" "$w/lower_fit.blend" --python "$d/lower/lower_rig.py" -- --out "$w/lower_rigged.blend" --module "$w/lower_module.blend"
"${B[@]}" "$base" --python "$d/lower/clavicle_finish.py" -- "$w/clavicle_finish.json"
"${B[@]}" "$w/hair_static.blend" --python "$d/assemble_c.py" -- "$w/assembled.blend" --top "$w/top_module.blend" \
    --lower "$w/lower_module.blend" --jewelry "$w/fitted_jewelry_R55.blend" --jewelry-col SUZU_TOP_JEWELRY \
    --body-patch "$w/clavicle_finish.json" --strict-weights
"${B[@]}" "$w/assembled.blend" --python "$d/toon_uniform.py" -- "$w/phase-c-pre-refinement.blend"
"${B[@]}" "$w/phase-c-pre-refinement.blend" --python "$d/assemble_round6.py" -- "$q/painted.blend"
"${B[@]}" "$q/painted.blend" --python "$d/motion.py" -- "$q/animated.blend" --stride 1 \
    --hair-module "$d/hair" --lower-module "$d/lower" --stats "$q/motion_stats.json"
"${B[@]}" "$q/animated.blend" --python "$d/export_c.py" -- "$q/assets"
python3 "$d/compact_weights.py" "$q/assets/suzu_v2_phaseC.glb" "$q/assets/suzu_v2_phaseC_compact.glb"
mv "$q/assets/suzu_v2_phaseC_compact.glb" "$q/assets/suzu_v2_phaseC.glb"
"${B[@]}" --python "$d/reopen_c.py" -- "$q/assets/suzu_v2_phaseC.glb" "$q/reopen.json"
touch "$q/ASSETS_OK"
if [ "${3:-}" = "--assets-only" ]; then exit 0; fi
"${B[@]}" "$q/painted.blend" --python "$d/studio_c.py" -- "$q/raw" stills --samples 27
python3 "$d/compose_c.py" "$q/raw" "$q/previews/v2_phaseC" --round6
bash "$d/render_motion_r6.sh" "$q/animated.blend" "$q/round6-motion"
cp "$q/round6-motion/previews/motion_expression_showcase.mp4" "$q/previews/v2_phaseC/"
