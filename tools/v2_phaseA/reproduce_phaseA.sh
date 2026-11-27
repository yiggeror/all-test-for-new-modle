#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
pixiv=$(realpath "$1")
donor=$(realpath "$2")
destination=$(mkdir -p "$3" && realpath "$3")
work="$destination/work"
mkdir -p "$work" "$work/raw"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-"${TMPDIR:-/tmp}/suzu_blender_config"}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"${TMPDIR:-/tmp}/suzu_blender_cache"}
export LP_NUM_THREADS=${LP_NUM_THREADS:-3}
B=(blender -b -t "${SUZU_THREADS:-4}" --python-exit-code 1)
"${B[@]}" --python "$here/head/inspect_base.py" -- "$pixiv" "$work/import"
"${B[@]}" "$work/import/base.blend" --python "$here/head/sculpt_phaseA.py" -- "$work/sculpt"
"${B[@]}" --python "$here/body/fit_phaseA.py" -- --input "$donor" --min-keys 57 --t-stage --out "$work/donor_T.blend"
"${B[@]}" --python "$here/body/fit_phaseA.py" -- --input "$work/sculpt/head_sculpt.blend" --vrm-metadata "$pixiv" --donor "$work/donor_T.blend" --out "$work/assembled.blend" --audit "$work/body.json"
WING_OUT="$work/wing_uv.json" "${B[@]}" "$work/sculpt/head_sculpt.blend" --python "$here/paint/wing_anchors.py"
python3 "$here/paint/make_textures.py" PixivTwist --eye-art "$work/wing_uv.json" --output "$work/paint"
"${B[@]}" "$work/assembled.blend" --python "$here/render_look.py" -- "$here/paint" "$here/head" "$work/paint" "$work/raw" --save "$work/painted.blend"
"${B[@]}" "$work/assembled.blend" --python "$here/body/studio_A.py" -- "$work/body_raw"
for item in front:000 threequarter:045 profile:090 back:180; do
  cp "$work/body_raw/${item%%:*}.png" "$work/raw/body_${item#*:}.png"
done
python3 "$here/compose.py" "$work/raw" "$destination/previews/v2_phaseA"
SUZU_EXPRESSIONS="$work/raw/expression_presets.json" SUZU_VRM_CONSTRAINTS="$here/native_constraints.json"   "${B[@]}" "$work/painted.blend" --python "$here/export_phase_a.py" -- "$destination/assets"

python3 "$here/verify_phase_a.py" "$destination" "$pixiv"
