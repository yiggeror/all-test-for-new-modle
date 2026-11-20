"""Synchronized 120.0s Spatialized Impressionist Soundtrack for Un Dimanche sur la Seine.

Built on CodePaint-Engine's anim.audio primitives (load, place, fade, wav) + scipy.signal:
  1. Two-movement Impressionist piano arc:
       - Acts I-III (0..83s): Debussy Premiere Arabesque (sunlit morning & breezy regatta)
       - Act IV   (76..120s): Ravel Pavane pour une infante defunte (sunset & twilight lanterns)
  2. 3D world-anchored spatial SFX driven by shots3.make_env(t):
       - Travelling meadow breeze & grass rustle modulated by env.wind()
       - Garden birdsong & wheeling swallows
       - Steam locomotive chugging + brass whistle (panning across viaduct + under-arch vault low-pass)
       - Hero sailboat hull splash & river current (panning as camera overtakes boat)
       - Guinguette terrace ambience & twilight pond/crickets
  3. Valley convolution reverb + soft broadcast peak limiting.
"""
import glob
import json
import os
import urllib.parse
import urllib.request
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from anim.audio import load as audio_load, place as audio_place, fade as audio_fade, wav as audio_wav
from shots3 import FILM_DUR, make_env
from actors3 import train_x_at, boat_pos_at
from scene_geom import river_x, river_hw

SR = 48000
N_SAMP = int(round(FILM_DUR * SR))

SOURCES = {
    "arabesque.ogg": "File:Claude Debussy - Première Arabesque - Patrizia Prati.ogg",
    "pavane.ogg": "File:Maurice Ravel - Thérèse Dussaut - Pavane pour une infante défunte.ogg",
    "birds.ogg": "File:Gentle breeze and birds singing.ogg",
    "river.ogg": "File:Shallow small river with stony riverbed.ogg",
    "train.ogg": "File:Train sounds from Iowa - Glaneur de sons.ogg",
    "whistle.ogg": "File:WWS SteamWhistle.ogg",
    "wind.ogg": "File:Wind sounds 2020-05-10 1625.mp3",
    "cafe.ogg": "File:Cafe ambiance.ogg",
    "pond.ogg": "File:Nature sounds ambience in a Dordogne pond.ogg",
}


def ensure_sources(cache_dir="/tmp/audio_v3"):
    os.makedirs(cache_dir, exist_ok=True)
    headers = {"User-Agent": "CodePaintV3Monet/1.0 (https://github.com/yiggeror/all-test-for-new-modle)"}
    for fname, title in SOURCES.items():
        path = os.path.join(cache_dir, fname)
        if os.path.exists(path) and os.path.getsize(path) > 8000:
            continue
        api = (
            "https://commons.wikimedia.org/w/api.php?action=query&titles="
            + urllib.parse.quote(title)
            + "&prop=imageinfo&iiprop=url&format=json"
        )
        req = urllib.request.Request(api, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
        url = next(iter(data["query"]["pages"].values()))["imageinfo"][0]["url"]
        req2 = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req2, timeout=45) as r2, open(path, "wb") as fh:
            fh.write(r2.read())
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


def _loop_fit(clip, length, xf_sec=1.5):
    n = len(clip)
    if n >= length:
        return clip[:length].copy()
    xf = min(int(xf_sec * SR), n // 4)
    out = np.zeros((length, 2), np.float32)
    pos = 0
    step = n - xf
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


def _reverb(x, rt=1.6, wet=0.32, seed=11):
    rng = np.random.default_rng(seed)
    n = int(rt * 1.4 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-6.9 * t / rt)[:, None]
    pre = int(0.015 * SR)
    ir[:pre] *= np.linspace(0.0, 1.0, pre, dtype=np.float32)[:, None]
    ir = _filt(ir, 220.0, 4600.0)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-9
    conv = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in (0, 1)], axis=1)
    return (x + wet * conv).astype(np.float32)


def _sample_camera_tracks(hz=20):
    ts = np.linspace(0.0, FILM_DUR, int(FILM_DUR * hz) + 1)
    C = np.zeros((len(ts), 3), np.float64)
    RT = np.zeros((len(ts), 3), np.float64)
    WIND = np.zeros(len(ts), np.float64)
    ST = np.zeros(len(ts), np.float64)
    for i, t in enumerate(ts):
        e = make_env(t)
        C[i] = e.C
        RT[i] = e.rt
        WIND[i] = float(e.wind(np.array([e.C[0]]), np.array([e.C[2]]))[0])
        ST[i] = e.t
    return ts, C, RT, WIND, ST


def _spatial_gain_pan(src_pos_fn, ts, C, RT, ref_dist=18.0):
    """Return sample-rate gainL and gainR envelopes from a 3D world-space moving sound source."""
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


def _env_curve(pts):
    p = np.array(pts, np.float64)
    t_samp = np.linspace(0.0, FILM_DUR, N_SAMP, endpoint=False)
    return np.interp(t_samp, p[:, 0], p[:, 1]).astype(np.float32)


def _synth_steam_chuff(ts, ST):
    """Synthesize rhythmic steam locomotive chuffing synchronized to train wheel speed."""
    t_samp = np.linspace(0.0, FILM_DUR, N_SAMP, endpoint=False, dtype=np.float64)
    rng = np.random.default_rng(91)
    noise = rng.standard_normal(N_SAMP).astype(np.float32)
    chuff_noise = _filt(np.column_stack([noise, noise]), 180.0, 1900.0)
    # 3.6 chuffs/sec modulated cleanly between t = 22..54s
    gate = np.maximum(0.0, np.sin(2.0 * np.pi * 3.6 * t_samp)) ** 3.0
    win = np.interp(t_samp, [20.0, 25.0, 50.0, 56.0], [0.0, 1.0, 1.0, 0.0])
    return (chuff_noise * (gate * win * 0.28).astype(np.float32)[:, None]).astype(np.float32)


def build_mix(out_wav="assets/audio/master_v3_120s.wav", cache_dir="/tmp/audio_v3"):
    ensure_sources(cache_dir)
    ts, C_trk, RT_trk, WIND_trk, ST_trk = _sample_camera_tracks(hz=20)
    t_samp = np.linspace(0.0, FILM_DUR, N_SAMP, endpoint=False)
    wind_samp = np.interp(t_samp, ts, WIND_trk).astype(np.float32)

    mix_buf = np.zeros((N_SAMP, 2), np.float32)

    # 1. Two-movement Impressionist Piano Arc
    arab = _norm_rms(audio_load(os.path.join(cache_dir, "arabesque.ogg"), SR)[int(0.8 * SR) :], -18.5)
    pavane = _norm_rms(audio_load(os.path.join(cache_dir, "pavane.ogg"), SR)[int(0.6 * SR) :], -19.0)

    arab_bed = _loop_fit(arab, N_SAMP, xf_sec=2.0)
    # Place Pavane starting gently around t=74s for sunset & twilight finale
    pav_bed = np.zeros((N_SAMP, 2), np.float32)
    audio_place(pav_bed, audio_fade(_loop_fit(pavane, int(52.0 * SR)), first=4.0, last=2.0, sr=SR), 73.0, SR, gain=1.0)

    g_arab = _env_curve([(0.0, 0.0), (2.5, 0.72), (73.0, 0.72), (83.0, 0.0), (120.0, 0.0)])
    g_pav = _env_curve([(0.0, 0.0), (73.0, 0.0), (83.0, 0.76), (114.0, 0.76), (120.0, 0.0)])

    # Gentle ducking (-2 dB) while passing right underneath the stone arch with train overhead (43..50s)
    duck = _env_curve([(0.0, 1.0), (42.0, 1.0), (45.0, 0.78), (49.0, 0.78), (52.0, 1.0), (120.0, 1.0)])
    music = (arab_bed * g_arab[:, None] + pav_bed * g_pav[:, None]) * duck[:, None]
    mix_buf += music

    # 2. Travelling Meadow Breeze modulated directly by Env.wind()
    wind_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "wind.ogg"), SR), 120.0, 3200.0), -26.0)
    wind_bed = _loop_fit(wind_raw, N_SAMP)
    g_wind = (0.14 + 0.34 * np.clip(wind_samp, 0.0, 1.2)) * _env_curve([(0.0, 0.6), (4.0, 1.0), (88.0, 0.7), (120.0, 0.3)])
    mix_buf += wind_bed * g_wind[:, None]

    # 3. Morning Garden Birdsong & Wheeling Swallows (Acts I & III)
    birds_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "birds.ogg"), SR), 750.0, 7800.0), -25.0)
    birds_bed = _loop_fit(birds_raw, N_SAMP)
    g_birds = _env_curve([(0.0, 0.0), (3.0, 0.36), (26.0, 0.34), (36.0, 0.14), (72.0, 0.28), (85.0, 0.16), (95.0, 0.0)])
    mix_buf += birds_bed * g_birds[:, None]

    # 4. 3D Spatialized Steam Locomotive + Under-Arch Low-Pass Rumble + Valley Whistle
    train_field = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "train.ogg"), SR), 70.0, 4200.0), -20.0)
    train_loop = _loop_fit(train_field, N_SAMP) * 0.45 + _synth_steam_chuff(ts, ST_trk) * 0.65
    gl_t, gr_t = _spatial_gain_pan(lambda t: np.array([train_x_at(t), 15.5, 215.0]), ts, C_trk, RT_trk, ref_dist=28.0)
    train_spat = np.column_stack([train_loop[:, 0] * gl_t, train_loop[:, 1] * gr_t])
    # Stone-arch muffling when camera flies underneath (44..49s)
    under_w = _env_curve([(0.0, 0.0), (43.0, 0.0), (45.2, 1.0), (48.0, 1.0), (50.2, 0.0), (120.0, 0.0)])[:, None]
    train_muffled = _filt(train_spat, 55.0, 360.0)
    mix_buf += train_spat * (1.0 - 0.72 * under_w) + train_muffled * (0.95 * under_w)

    # Brass steam whistles echoing across the Seine valley at t=32.5s and t=40.5s
    whistle_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "whistle.ogg"), SR), 280.0, 4800.0), -22.0)
    whistle_wet = _reverb(audio_fade(whistle_raw[: int(2.6 * SR)], first=0.05, last=0.35, sr=SR), rt=1.8, wet=0.55)
    audio_place(mix_buf, whistle_wet, 32.5, SR, gain=0.42, pan=-0.38)
    audio_place(mix_buf, whistle_wet, 40.5, SR, gain=0.48, pan=0.12)

    # 5. Seine River Current & Spatialized Hero Sailboat Bow Wash (panning as camera overtakes!)
    river_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "river.ogg"), SR), 180.0, 5200.0), -26.0)
    river_bed = _loop_fit(river_raw, N_SAMP)
    g_river = _env_curve([(0.0, 0.06), (26.0, 0.24), (54.0, 0.28), (85.0, 0.22), (114.0, 0.14), (120.0, 0.0)])
    mix_buf += river_bed * g_river[:, None]

    gl_b, gr_b = _spatial_gain_pan(lambda t: boat_pos_at(0, t), ts, C_trk, RT_trk, ref_dist=14.0)
    g_boat_act = _env_curve([(0.0, 0.0), (50.0, 0.0), (55.0, 0.55), (72.0, 0.45), (78.0, 0.0), (120.0, 0.0)])
    mix_buf += np.column_stack([river_bed[:, 0] * gl_b, river_bed[:, 1] * gr_b]) * g_boat_act[:, None]

    # 6. Guinguette Cafe Terrace Ambience & Twilight Pond Crickets (Act IV)
    cafe_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "cafe.ogg"), SR), 220.0, 3800.0), -25.0)
    cafe_bed = _loop_fit(cafe_raw, N_SAMP)
    cafe_pos = np.array([float(river_x(406.0) + river_hw(406.0)) + 14.0, 3.0, 406.0])
    gl_c, gr_c = _spatial_gain_pan(lambda t: cafe_pos, ts, C_trk, RT_trk, ref_dist=26.0)
    g_cafe_act = _env_curve([(0.0, 0.0), (78.0, 0.0), (86.0, 0.42), (103.0, 0.36), (115.0, 0.14), (120.0, 0.0)])
    mix_buf += np.column_stack([cafe_bed[:, 0] * gl_c, cafe_bed[:, 1] * gr_c]) * g_cafe_act[:, None]

    pond_raw = _norm_rms(_filt(audio_load(os.path.join(cache_dir, "pond.ogg"), SR), 240.0, 6800.0), -26.0)
    pond_bed = _loop_fit(pond_raw, N_SAMP)
    g_pond = _env_curve([(0.0, 0.0), (88.0, 0.0), (96.0, 0.32), (115.0, 0.28), (120.0, 0.0)])
    mix_buf += pond_bed * g_pond[:, None]

    # 7. Smooth Opening & Closing Fades + Soft Broadcast Peak Limiter
    fin = int(2.2 * SR)
    fout = int(4.5 * SR)
    mix_buf[:fin] *= np.linspace(0.0, 1.0, fin, dtype=np.float32)[:, None] ** 1.4
    mix_buf[-fout:] *= np.linspace(1.0, 0.0, fout, dtype=np.float32)[:, None] ** 1.6

    peak = float(np.max(np.abs(mix_buf)))
    if peak > 0.86:
        mix_buf = (np.tanh(mix_buf / peak * 1.15) * 0.85).astype(np.float32)

    out_path = audio_wav(mix_buf, out_wav, sr=SR)
    print(f"Wrote synchronized 120.0s spatial mix -> {out_path} ({os.path.getsize(out_path) / 1e6:.2f} MB)")
    return str(out_path)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/audio/master_v3_120s.wav"
    build_mix(out)
