"""Synchronized 96.0s Impressionist Audio Mix for Les Heures de Lumiere.

Combines:
1. Claude Debussy - Premiere Arabesque (Patrizia Prati, CC BY-SA 4.0)
2. Scene-matched field recordings from Wikimedia Commons (waves, garden birds,
   distant cathedral bells, evening pond/crickets)
3. Subtle procedural breeze texture driven directly by Env.wind(camX)

Outputs 48 kHz 16-bit stereo WAV (exact 96.000s = 4,608,000 samples).
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import Env, DUR, scene_of

SR = 48000
NSAMP = int(round(DUR * SR))

SOURCES = {
    "arabesque.ogg": "File:Claude_Debussy_-_Première_Arabesque_-_Patrizia_Prati.ogg",
    "waves.ogg": "File:Oceanwavescrushing.ogg",
    "garden_birds.ogg": "File:Birds_singing_in_garden.ogg",
    "bells.ogg": "File:Churchbells.ogg",
    "dusk_pond.ogg": "File:Nature_sounds_ambience_in_a_Dordogne_pond.ogg",
}


def ensure_sources(cache_dir="/tmp/audio_src"):
    os.makedirs(cache_dir, exist_ok=True)
    headers = {"User-Agent": "AntigravityMonetProject/1.0 (https://github.com/yiggeror/all-test-for-new-modle)"}
    for fname, title in SOURCES.items():
        path = os.path.join(cache_dir, fname)
        if os.path.exists(path) and os.path.getsize(path) > 10000:
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
        with urllib.request.urlopen(req2, timeout=45) as r2, open(path, "wb") as f:
            f.write(r2.read())
    return cache_dir


def decode_ffmpeg(path, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd.extend(["-af", af])
    cmd.extend(["-ar", str(SR), "-ac", "2", "-f", "f32le", "pipe:1"])
    raw = subprocess.check_output(cmd)
    arr = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    return arr


def fit_loop(arr, length, xf_sec=2.0):
    """Loop an audio clip seamlessly to desired sample length with equal-power crossfade."""
    n = len(arr)
    if n >= length:
        return arr[:length].copy()
    xf = min(int(xf_sec * SR), n // 4)
    out = np.zeros((length, 2), dtype=np.float32)
    pos = 0
    step = n - xf
    first = True
    while pos < length:
        rem = length - pos
        take = min(n, rem)
        seg = arr[:take].copy()
        if not first and xf > 0:
            k = min(xf, take)
            w = np.linspace(0.0, 1.0, k, dtype=np.float32)[:, None]
            seg[:k] *= np.sin(w * np.pi * 0.5)
            out[pos : pos + k] *= np.cos(w * np.pi * 0.5)
        out[pos : pos + take] += seg
        pos += step
        first = False
    return out


def wind_synth(seed=99):
    """Subtle stereo breeze modulated directly by the world wind field Env.wind()."""
    rng = np.random.default_rng(seed)
    t_grid = np.linspace(0.0, DUR, int(DUR * 10) + 1, dtype=np.float64)
    w_ctrl = np.array([float(Env(tt).wind(Env(tt).camX, 1.0)) for tt in t_grid], dtype=np.float64)
    t_samp = np.linspace(0.0, DUR, NSAMP, endpoint=False, dtype=np.float64)
    w_env = np.interp(t_samp, t_grid, w_ctrl).astype(np.float32)

    stereo = np.zeros((NSAMP, 2), dtype=np.float32)
    freqs = np.fft.rfftfreq(NSAMP, d=1.0 / SR)
    band = np.exp(-0.5 * ((freqs - 360.0) / 180.0) ** 2) * (freqs > 70.0)
    for ch in range(2):
        white = rng.standard_normal(NSAMP).astype(np.float32)
        breeze = np.fft.irfft(np.fft.rfft(white) * band, n=NSAMP).astype(np.float32)
        breeze /= np.std(breeze) + 1e-8
        stereo[:, ch] = breeze * (0.012 + 0.024 * np.clip(w_env, 0.0, 1.0))
    return stereo


def scene_weights():
    t = np.linspace(0.0, DUR, NSAMP, endpoint=False, dtype=np.float64)
    t_ctrl = np.linspace(0.0, DUR, 481)
    d_ctrl = np.array([scene_of(Env(tt).camX) for tt in t_ctrl], dtype=np.float64)
    d = np.interp(t, t_ctrl, d_ctrl).astype(np.float32)

    def win(k, soft=0.95):
        w = np.clip(1.0 - np.abs(d - k) / soft, 0.0, 1.0)
        return (w * w * (3.0 - 2.0 * w)).astype(np.float32)[:, None]

    return win(0.0), win(1.0), win(2.0), win(3.0), win(4.0)


def build_mix(out_wav="assets/audio/master_96s.wav", cache_dir="/tmp/audio_src"):
    ensure_sources(cache_dir)

    # 1. Main piano bed: Debussy Arabesque I (skip first 0.6s hall noise, take 96s)
    piano = decode_ffmpeg(os.path.join(cache_dir, "arabesque.ogg"), af="atrim=start=0.5,highpass=f=45")
    piano = fit_loop(piano, NSAMP)
    piano /= np.max(np.abs(piano)) + 1e-8

    # 2. Scene ambiences (gently band-shaped so they never clash with piano)
    waves = fit_loop(decode_ffmpeg(os.path.join(cache_dir, "waves.ogg"), af="lowpass=f=3600,highpass=f=80"), NSAMP)
    waves /= np.std(waves) + 1e-8

    birds = fit_loop(decode_ffmpeg(os.path.join(cache_dir, "garden_birds.ogg"), af="highpass=f=900,lowpass=f=7500"), NSAMP)
    birds /= np.std(birds) + 1e-8

    bells = fit_loop(decode_ffmpeg(os.path.join(cache_dir, "bells.ogg"), af="lowpass=f=2200,highpass=f=140"), NSAMP)
    bells /= np.std(bells) + 1e-8

    pond = fit_loop(decode_ffmpeg(os.path.join(cache_dir, "dusk_pond.ogg"), af="highpass=f=180,lowpass=f=6000"), NSAMP)
    pond /= np.std(pond) + 1e-8

    w0, w1, w2, w3, w4 = scene_weights()
    amb = (
        0.042 * w0 * waves
        + 0.018 * w1 * waves
        + 0.032 * w2 * birds
        + 0.022 * w3 * bells
        + 0.030 * w4 * pond
        + 0.65 * wind_synth()
    )

    mix_buf = 0.56 * piano + amb

    # Smooth head fade-in (1.8s) and tail fade-out (4.2s matching linen canvas fade)
    fin = int(1.8 * SR)
    fout = int(4.2 * SR)
    mix_buf[:fin] *= np.linspace(0.0, 1.0, fin, dtype=np.float32)[:, None] ** 1.4
    mix_buf[-fout:] *= np.linspace(1.0, 0.0, fout, dtype=np.float32)[:, None] ** 1.6

    # Gentle soft limiter below -1 dBFS
    peak = float(np.max(np.abs(mix_buf)))
    if peak > 0.88:
        mix_buf = np.tanh(mix_buf / peak * 1.15) * 0.86

    pcm16 = np.clip(mix_buf * 32767.0, -32768.0, 32767.0).astype(np.int16)
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())
    print(f"Wrote synchronized 96.0s mix -> {out_wav} ({os.path.getsize(out_wav) / 1e6:.2f} MB)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/audio/master_96s.wav"
    build_mix(out)
