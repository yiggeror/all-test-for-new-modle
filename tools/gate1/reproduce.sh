#!/bin/bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(realpath "$here/../..")
dest=$(mkdir -p "${1:-$repo/dist/gate1}" && realpath "${1:-$repo/dist/gate1}")
mods="$dest/modules"; mkdir -p "$mods/head"
blender -b -t 4 --python-exit-code 1 --python "$here/head/build_head.py" -- "$mods/head" "--reference=$repo/references/03_face_expressions_props.jpg"
cp "$mods/head/suzu_head.blend" "$mods/head.blend"
blender -b -t 3 --python-exit-code 1 --python "$here/body/body_model.py" -- "$mods/body_base.blend"
blender -b "$mods/body_base.blend" -t 3 --python-exit-code 1 --python "$here/body/fit_r25.py" -- "$mods/body_pose.blend"
blender -b "$mods/body_pose.blend" -t 3 --python-exit-code 1 --python "$here/body/fit_neck_r25.py" -- "$mods/body.blend"
SUZU_GARMENT_DIR="$mods" SUZU_STAGE=freeze blender -b -t 3 --python-exit-code 1 --python "$here/garment/build.py"
bash "$here/make_review.sh" "$mods" "$dest"
python3 "$here/check.py" "$dest"
