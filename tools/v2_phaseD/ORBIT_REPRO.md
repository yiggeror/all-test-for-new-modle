# Suzu Hoshino · Phase D 360° master

The signed Round 6 source file `assets/suzu_v2_phaseC.blend` is unchanged:

`46742cebd80b1bfb46413cf787d6769b27c48663160bfa84077545156aed2962`

An orbit is a static neutral pose with only the camera moving. For frames
1–240 the camera covers a full-body turn at a 1.5° step. Frames 241–360
start at the front again and cover a second full turn at a 3° step,
framed around the upper body instead of zooming footage. The asset retains
the signed skin, polished Mary Janes, and the tucked Oxford / thicker braid.

## Regenerate

Blender (4.3.2 used here), FFmpeg with libx264, Python with Pillow and NumPy:

```sh
export BASE=/absolute/path/approved/assets/suzu_v2_phaseC.blend
export STUDIO=/absolute/path/approved/tools/v2_phaseC/studio_c.py
export ORBIT_DIR=/path/to/a/clean/temporary/directory
./run_render.sh
python pack_orbit.py "$ORBIT_DIR/frames" "$ORBIT_DIR/turntable_final_1080p.mp4"
python verify_orbit.py "$ORBIT_DIR/turntable_final_1080p.mp4" --record "$ORBIT_DIR/orbit_verified.json"
```

The runner renders each actual pose/camera state on the signed asset at an
adaptive ceiling of 8 Cycles samples. The border opt-in saves rendering of
flat studio background off to either side. The packer first verifies that
both crop edges contain only the world colour, adds back the checked world
columns to the original 1920-wide canvas, and encodes without scaling,
interpolation, blanks, or neighboring-frame substitution. It emits a raw
RGB hash and the camera angle for each of 360 frames.

The export is silent H.264 with BT.709 metadata at 1920 × 1080 / 30 fps,
with a progressive MP4 start. The QC decodes every frame and writes
per-frame MD5s, reports duplicates, and checks dimensions and exact
duration.
