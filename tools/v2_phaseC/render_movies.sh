#!/usr/bin/env bash
set -euo pipefail
q=$(realpath "$1")
for i in $(seq 1 72); do
    [ -f "$q/ASSETS_OK" ] && break
    sleep 5
done
test -f "$q/ASSETS_OK"
python3 - "$q/reopen.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert x['bones']>=183 and x['garments']==85
fail=[(r['frame'],r['hair_vs_clothing_and_skin']) for r in x['checks'] if r.get('hair_vs_clothing_and_skin')]
if fail:raise SystemExit(f'Reopened glTF collision needs inspection: {fail}')
print('Reopened GLB peak frames: no hair/wear/skin surface intersection in chosen six poses.',flush=True)
PY
mkdir -p "$q/movie_frames"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-"${TMPDIR:-/tmp}/suzu_config"}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-"${TMPDIR:-/tmp}/suzu_cache"}
export LP_NUM_THREADS=2
B=(blender -b -t "${SUZU_JOB_THREADS:-2}" --python-exit-code 1)
count=0
pids=()
for spec in "orbit:1:180" "orbit:181:360" "motion:1:171" "motion:172:342"; do
    IFS=: read -r kind ff fl <<<"$spec"
    file="$q/painted.blend";[ "$kind" != motion ] || file="$q/animated.blend"
    "${B[@]}" "$file" --python "$q/impl/studio_c.py" -- "$q/movie_frames" "$kind"        --start "$ff" --end "$fl" --samples 7 --movie-border 1120 >"$q/$kind-$ff-$fl.log" 2>&1 &
    pids+=($!);((++count))
done
touch "$q/MOVIES_STARTED"
ok=0
for pid in "${pids[@]}"; do
    wait "$pid" || ok=1
done
test "$ok" -eq 0
python3 "$q/impl/encode_movies.py" "$q/movie_frames" "$q/previews/v2_phaseC" | tee "$q/movie_verify.log"
touch "$q/MOVIES_OK"
