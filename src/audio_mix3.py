"""Synchronized 120.0s Spatialized Soundtrack for Un Dimanche sur la Seine.

100% genuine high-quality classical recordings and field SFX (zero synthesized sound):
  Music:
    - Acts I-III (0..83s): Claude Debussy - Premiere Arabesque (Patrizia Prati, CC BY-SA 4.0)
    - Act IV   (74..120s): Maurice Ravel - Pavane pour une infante defunte (Therese Dussaut, CC BY-SA 2.0)
  Spatial Field SFX (all 3D world-anchored via shots3.make_env(t)):
    - Meadow breeze (Wind sounds 2020-05-10) modulated by Env.wind()
    - Morning Eurasian Skylark & garden birds (Act I poppy hillside)
    - Playful dog barks spatialized to the bounding terrier (Act I)
    - Real steam locomotive chuffing (Cogwheel loco Rigi + Iowa train) + brass steam whistle
      with stereo viaduct panning and stone-arch vault low-pass muffling (Act II)
    - Real river current, water waves & Barn Swallows swooping over sailboats (Act III)
    - French Guinguette cafe terrace ambience, distant village evening church bells,
      and Dordogne twilight pond crickets (Act IV)
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from anim.audio import load as audio_load, place as audio_place, fade as audio_fade, wav as audio_wav
from shots3 import FILM_DUR, make_env
from actors3 import boy_pos_at, train_x_at, boat_pos_at
from scene_geom import river_x, river_hw

SR = 48000
N_SAMP = int(round(FILM_DUR * SR))

SOURCES = {
    "arabesque.ogg": "File:Claude Debussy - Première Arabesque - Patrizia Prati.ogg",
    "pavane.ogg": "File:Maurice Ravel - Thérèse Dussaut - Pavane pour une infante défunte.ogg",
    "skylark.mp3": "File:Alauda arvensis - Eurasian Skylark XC528350.mp3",
    "birds.ogg": "File:Gentle breeze and birds singing.ogg",
    "dog.ogg": "File:Barking of a dog 2.ogg",
    "steam_chuff.ogg": "File:Cogwheel loco Rigi vsb.ogg",
    "train_pass.ogg": "File:Train sounds from Iowa - Glaneur de sons.ogg",
    "whistle.ogg": "File:WWS SteamWhistle.ogg",
    "river.ogg": "File:Shallow small river with stony riverbed.ogg",
    "waves.ogg": "File:Water wave.ogg",
    "swallows.mp3": "File:Hirundo rustica - Barn Swallow XC254488.mp3",
    "wind.mp3": "File:Wind sounds 2020-05-10 1625.mp3",
    "cafe.ogg": "File:Cafe ambiance.ogg",
    "bells.wav": "File:Church bells evening, parish church Waidring.wav",
    "pond.ogg": "File:Nature sounds ambience in a Dordogne pond.ogg",
}


def ensure_sources(cache_dir="/tmp/audio_v3"):
    import time
    os.makedirs(cache_dir, exist_ok=True)
    headers = {"User-Agent": "CodePaintV3Monet/1.0 (https://github.com/yiggeror/all-test-for-new-modle; educational-art)"}
    missing = {fname: title for fname, title in SOURCES.items()
               if not (os.path.exists(os.path.join(cache_dir, fname)) and os.path.getsize(os.path.join(cache_dir, fname)) > 8000)}
    if not missing:
        return cache_dir

    # Single batched API call for all missing titles
    api = (
        "https://commons.wikimedia.org/w/api.php?action=query&titles="
        + urllib.parse.quote("|".join(missing.values()))
        + "&prop=imageinfo&iiprop=url&format=json"
    )
    req = urllib.request.Request(api, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode())
    norm_map = {n["from"]: n["to"] for n in data.get("query", {}).get("normalized", [])}
    url_by_title = {}
    for page in data.get("query", {}).get("pages", {}).values():
        if "imageinfo" in page:
            url_by_title[page["title"]] = page["imageinfo"][0]["url"]

    for fname, title in missing.items():
        path = os.path.join(cache_dir, fname)
        resolved = norm_map.get(title, title)
        url = url_by_title[resolved]
        for attempt in range(5):
            try:
                time.sleep(1.5 + attempt * 2.0)
                req2 = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req2, timeout=60) as r2:
                    blob = r2.read()
                tmp = path + ".tmp"
                with open(tmp, "wb") as fh:
                    fh.write(blob)
                os.replace(tmp, path)
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 503, 502) and attempt < 4:
                    wait_s = int(e.headers.get("Retry-After", 8 * (attempt + 1)))
                    time.sleep(min(wait_s, 45))
                    continue
                raise
    return cache_dir


def _filt(x, lo=None, hi=None, order=2):
    y = np.asarray(x, np.float32)
    if lo is not None:
        y = sosfilt(butter(order, lo, "hp", fs=SR, output="sos"), y, axis=0)
    if hi is not None:
        y = sosfilt(butter(order, hi, "lp", fs=SR, output="sos"), y, axis=0)
    return y.astype(np.float32)


def _norm_rms(x, target_db=-24.0):
    rms = float(np.sqrt(np.mean(x ** 2)) + 1e-9)
    return (x * ((10.0 ** (target_db / 20.0)) / rms)).astype(np.float32)


def _tame(x, ceil_db=-14.0):
    c = 10.0 ** (ceil_db / 20.0)
    return (np.tanh(x / c) * c).astype(np.float32)


def _loop_fit(clip, length, xf_sec=1.2):
    n = len(clip)
    if n >= length:
        return clip[:length].copy()
    xf = min(int(xf_sec * SR), max(1, n // 4))
    out = np.zeros((length, 2), np.float32)
    pos = 0
    step = max(1, n - xf)
    first = True
    while pos < length:
        take = min(n, length - pos)
        seg = clip[:take].copy()
        if not first and xf > 0:
            k = min(xf, take)
            w = np.linspace(0.0, 1.0, k, dtype=np.float32)[:, None]
            seg[:k] *= np.sin(w * np.pi * 0.5)
            out[pos : pos + k] *= np.cos(w * np.pi * 0.5)
        out[pos : pos + take] += seg
        pos += step
        first = False
    return out


def _reverb(x, rt=1.7, wet=0.45, seed=11):
    rng = np.random.default_rng(seed)
    n = int(rt * 1.4 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-6.9 * t / rt)[:, None]
    pre = int(0.016 * SR)
    ir[:pre] *= np.linspace(0.0, 1.0, pre, dtype=np.float32)[:, None]
    ir = _filt(ir, 200.0, 4400.0)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-9
    conv = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in (0, 1)], axis=1)
    return (x + wet * conv).astype(np.float32)


def _sample_camera_tracks(hz=20):
    ts = np.linspace(0.0, FILM_DUR, int(FILM_DUR * hz) + 1)
    C = np.zeros((len(ts), 3), np.float64)
    RT = np.zeros((len(ts), 3), np.float64)
    WIND = np.zeros(len(ts), np.float64)
    for i, t in enumerate(ts):
        e = make_env(t)
        C[i] = e.C
        RT[i] = e.rt
        WIND[i] = float(e.wind(np.array([e.C[0]]), np.array([e.C[2]]))[0])
    return ts, C, RT, WIND


def _spatial_gain_pan(src_pos_fn, ts, C, RT, ref_dist=18.0):
    gl = np.zeros(len(ts), np.float32)
    gr = np.zeros(len(ts), np.float32)
    for i, t in enumerate(ts):
        sp = src_pos_fn(t)
        dvec = sp - C[i]
        dist = float(np.linalg.norm(dvec)) + 1e-6
        atten = 1.0 / (1.0 + (dist / ref_dist) ** 1.65)
        pan = float(np.clip(np.dot(dvec, RT[i]) / (dist * 0.78 + 3.0), -0.90, 0.90))
        gl[i] = atten * min(1.0, 1.0 - pan)
        gr[i] = atten * min(1.0, 1.0 + pan)
    t_samp = np.linspace(0.0, FILM_DUR, N_SAMP, endpoint=False)
    return np.interp(t_samp, ts, gl).astype(np.float32), np.interp(t_samp, ts, gr).astype(np.float32)


def _pan_at(pos_world, t_film):
    e = make_env(t_film)
    dvec = np.asarray(pos_world, np.float64) - e.C
    dist = float(np.linalg.norm(dvec)) + 1e-6
    pan = float(np.clip(np.dot(dvec, e.rt) / (dist * 0.78 + 3.0), -0.88, 0.88))
    atten = 1.0 / (1.0 + (dist / 22.0) ** 1.5)
    return pan, atten


def _env_curve(pts):
    p = np.array(pts, np.float64)
    t_samp = np.linspace(0.0, FILM_DUR, N_SAMP, endpoint=False)
    return np.interp(t_samp, p[:, 0], p[:, 1]).astype(np.float32)


def build_mix(out_wav="assets/audio/master_v3_120s.wav", cache_dir="/tmp/audio_v3"):
    ensure_sources(cache_dir)
    ts, C_trk, RT_trk, WIND_trk = _sample_camera_tracks(hz=20)
    t_samp = np.linspace(0.0, FILM_DUR, N_SAMP, endpoint=False)
    wind_samp = np.interp(t_samp, ts, WIND_trk).astype(np.float32)

    mix_buf = np.zeros((N_SAMP, 2), np.float32)

    # 1. Two-Movement Impressionist Piano Arc (100% genuine performances)
    arab = _norm_rms(audio_load(os.path.join(cache_dir, "arabesque.ogg"), SR)[int(0.8 * SR) :], -18.0)
    pavane = _norm_rms(audio_load(os.path.join(cache_dir, "pavane.ogg"), SR)[int(0.6 * SR) :], -18.5)

    arab_bed = _loop_fit(arab, N_SAMP, xf_sec=2.0)
    pav_bed = np.zeros((N_SAMP, 2), np.float32)
    audio_place(pav_bed, audio_fade(_loop_fit(pavane, int(52.0 * SR)), first=4.5, last=2.0, sr=SR), 73.0, SR, gain=1.0)

    g_arab = _env_curve([(0.0, 0.0), (2.5, 0.72), (73.0, 0.72), (83.0, 0.0), (120.0, 0.0)])
    g_pav = _env_curve([(0.0, 0.0), (73.0, 0.0), (83.0, 0.76), (114.0, 0.76), (120.0, 0.0)])
    duck = _env_curve([(0.0, 1.0), (42.0, 1.0), (45.0, 0.76), (49.0, 0.76), (52.0, 1.0), (120.0, 1.0)])
    mix_buf += (arab_bed * g_arab[:, None] + pav_bed * g_pav[:, None]) * duck[:, None]

    # 2. Travelling Outdoor Wind (real field recording modulated by Env.wind())
    wind_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "wind.mp3"), SR), 110.0, 2800.0), -26.0))
    wind_bed = _loop_fit(wind_raw, N_SAMP)
    g_wind = (0.14 + 0.34 * np.clip(wind_samp, 0.0, 1.2)) * _env_curve([(0.0, 0.5), (4.0, 1.0), (86.0, 0.65), (120.0, 0.25)])
    mix_buf += wind_bed * g_wind[:, None]

    # 3. Act I Meadow Skylark, Garden Birds & Spatialized Playful Dog Barks
    birds_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "birds.ogg"), SR), 700.0, 7600.0), -25.0))
    skylark_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "skylark.mp3"), SR), 1200.0, 8200.0), -23.5))
    mix_buf += _loop_fit(birds_raw, N_SAMP) * _env_curve([(0.0, 0.0), (3.0, 0.34), (28.0, 0.28), (44.0, 0.10), (72.0, 0.22), (92.0, 0.0)])[:, None]
    mix_buf += _loop_fit(skylark_raw, N_SAMP, xf_sec=0.8) * _env_curve([(0.0, 0.0), (4.0, 0.30), (24.0, 0.26), (32.0, 0.0)])[:, None]

    dog_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "dog.ogg"), SR), 320.0, 4200.0), -23.0))
    dog_clip = audio_fade(dog_raw[: int(1.6 * SR)], first=0.04, last=0.18, sr=SR)
    for tb in (9.5, 16.8):
        pan_d, att_d = _pan_at(boy_pos_at(tb), tb)
        audio_place(mix_buf, _reverb(dog_clip, rt=0.9, wet=0.25), tb, SR, gain=0.35 * max(0.35, att_d), pan=pan_d)

    # 4. Act II Real Steam Locomotive + Under-Arch Vault Low-Pass + Echoing Valley Brass Whistle
    chuff_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "steam_chuff.ogg"), SR), 75.0, 4200.0), -19.5))
    pass_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "train_pass.ogg"), SR), 65.0, 3800.0), -21.0))
    train_real = _loop_fit(chuff_raw, N_SAMP, xf_sec=0.8) * 0.72 + _loop_fit(pass_raw, N_SAMP, xf_sec=1.5) * 0.42
    gl_t, gr_t = _spatial_gain_pan(lambda t: np.array([train_x_at(t), 15.5, 215.0]), ts, C_trk, RT_trk, ref_dist=30.0)
    train_spat = np.column_stack([train_real[:, 0] * gl_t, train_real[:, 1] * gr_t])
    under_w = _env_curve([(0.0, 0.0), (43.0, 0.0), (45.2, 1.0), (48.0, 1.0), (50.2, 0.0), (120.0, 0.0)])[:, None]
    train_muffled = _filt(train_spat, 50.0, 360.0)
    train_gate = _env_curve([(0.0, 0.0), (20.0, 0.0), (26.0, 1.0), (52.0, 0.85), (58.0, 0.0), (120.0, 0.0)])[:, None]
    mix_buf += (train_spat * (1.0 - 0.72 * under_w) + train_muffled * (0.95 * under_w)) * train_gate

    whistle_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "whistle.ogg"), SR), 280.0, 4800.0), -22.0)
    whistle_wet = _reverb(audio_fade(whistle_raw[: int(2.6 * SR)], first=0.05, last=0.35, sr=SR), rt=1.8, wet=0.55)
    for tw in (32.5, 40.5):
        pan_w, _ = _pan_at(np.array([train_x_at(tw), 16.5, 215.0]), tw)
        audio_place(mix_buf, whistle_wet, tw, SR, gain=0.45, pan=pan_w)

    # 5. Act III Seine Water Waves, River Current, Sailboat Wake & Barn Swallows
    river_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "river.ogg"), SR), 180.0, 5000.0), -25.5))
    waves_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "waves.ogg"), SR), 120.0, 4800.0), -24.5))
    swallows_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "swallows.mp3"), SR), 1400.0, 8000.0), -24.5))

    river_bed = _loop_fit(river_raw, N_SAMP)
    waves_bed = _loop_fit(waves_raw, N_SAMP)
    mix_buf += river_bed * _env_curve([(0.0, 0.04), (26.0, 0.22), (54.0, 0.25), (85.0, 0.20), (114.0, 0.12), (120.0, 0.0)])[:, None]

    gl_b, gr_b = _spatial_gain_pan(lambda t: boat_pos_at(0, t), ts, C_trk, RT_trk, ref_dist=15.0)
    g_boat_act = _env_curve([(0.0, 0.0), (50.0, 0.0), (55.0, 0.58), (72.0, 0.48), (79.0, 0.0), (120.0, 0.0)])
    mix_buf += np.column_stack([waves_bed[:, 0] * gl_b, waves_bed[:, 1] * gr_b]) * g_boat_act[:, None]
    mix_buf += _loop_fit(swallows_raw, N_SAMP) * _env_curve([(0.0, 0.0), (50.0, 0.0), (58.0, 0.28), (74.0, 0.24), (84.0, 0.0), (120.0, 0.0)])[:, None]

    # 6. Act IV Guinguette Cafe Ambience, Evening Church Bells & Dordogne Pond Crickets
    cafe_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "cafe.ogg"), SR), 220.0, 3600.0), -25.0))
    cafe_bed = _loop_fit(cafe_raw, N_SAMP)
    cafe_pos = np.array([float(river_x(406.0) + river_hw(406.0)) + 14.0, 3.0, 406.0])
    gl_c, gr_c = _spatial_gain_pan(lambda t: cafe_pos, ts, C_trk, RT_trk, ref_dist=28.0)
    g_cafe_act = _env_curve([(0.0, 0.0), (78.0, 0.0), (86.0, 0.42), (103.0, 0.36), (115.0, 0.14), (120.0, 0.0)])
    mix_buf += np.column_stack([cafe_bed[:, 0] * gl_c, cafe_bed[:, 1] * gr_c]) * g_cafe_act[:, None]

    bells_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "bells.wav"), SR), 220.0, 3600.0), -23.5))
    bells_clip = _reverb(audio_fade(bells_raw[: int(24.0 * SR)], first=1.8, last=3.5, sr=SR), rt=2.2, wet=0.45)
    church_pos = np.array([float(river_x(418.0) + river_hw(418.0)) + 66.0, 14.0, 418.0])
    pan_ch, _ = _pan_at(church_pos, 96.0)
    audio_place(mix_buf, bells_clip, 91.0, SR, gain=0.22, pan=pan_ch)

    pond_raw = _tame(_norm_rms(_filt(audio_load(os.path.join(cache_dir, "pond.ogg"), SR), 240.0, 6800.0), -25.5))
    pond_bed = _loop_fit(pond_raw, N_SAMP)
    mix_buf += pond_bed * _env_curve([(0.0, 0.0), (88.0, 0.0), (96.0, 0.34), (115.0, 0.28), (120.0, 0.0)])[:, None]

    # 7. Smooth Opening & Closing Fades + Soft Broadcast Peak Limiter
    fin = int(2.2 * SR)
    fout = int(4.5 * SR)
    mix_buf[:fin] *= np.linspace(0.0, 1.0, fin, dtype=np.float32)[:, None] ** 1.4
    mix_buf[-fout:] *= np.linspace(1.0, 0.0, fout, dtype=np.float32)[:, None] ** 1.6

    peak = float(np.max(np.abs(mix_buf)))
    if peak > 0.86:
        mix_buf = (np.tanh(mix_buf / peak * 1.15) * 0.85).astype(np.float32)

    out_path = audio_wav(mix_buf, out_wav, sr=SR)
    print(f"Wrote 100% genuine-recording 120.0s spatial mix -> {out_path} ({os.path.getsize(out_path) / 1e6:.2f} MB)")
    return str(out_path)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/audio/master_v3_120s.wav"
    build_mix(out)
