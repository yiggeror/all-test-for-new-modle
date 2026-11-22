"""100% Genuine Classical Score & Field SFX Audio Mixer for Monet v4 (120.0s, 48kHz Stereo)."""
import os
import time
import json
import urllib.parse
import urllib.request
import subprocess
import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 48000
DUR = 120.0
N_SAMPLES = int(round(DUR * SR))

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache_audio_v4")

# Curated Wikimedia Commons genuine music & field recordings (zero synthesized SFX)
SOURCES = {
    # Classical Impressionist Music (100% Genuine Performances)
    "debussy_arabesque1": {
        "titles": ["File:Claude Debussy - Première Arabesque - Patrizia Prati.ogg"],
        "search": "Debussy Premiere Arabesque filetype:audio",
    },
    "debussy_cathedrale": {
        "titles": ["File:La Cathédrale engloutie - Claude Debussy - performed by Ivan Ilic.ogg"],
        "search": "Cathedrale engloutie Debussy filetype:audio",
    },
    "ravel_pavane": {
        "titles": ["File:Maurice Ravel - Thérèse Dussaut - Pavane pour une infante défunte.ogg"],
        "search": "Pavane pour une infante defunte filetype:audio",
    },
    # Natural Field Recordings & Authentic SFX
    "skylark": {
        "titles": ["File:Alauda arvensis - Eurasian Skylark XC484052.mp3"],
        "search": "Alauda arvensis Skylark filetype:audio",
    },
    "dog_bark": {
        "titles": ["File:Barking of a dog 2.ogg"],
        "search": "Barking of a dog filetype:audio",
    },
    "swallow": {
        "titles": ["File:Hirundo rustica - Barn Swallow - XC83449.ogg", "File:Hirundo rustica - Barn Swallow XC83449.mp3"],
        "search": "Hirundo rustica Barn Swallow filetype:audio",
    },
    "brook": {
        "titles": ["File:Brook sound.ogg"],
        "search": "Brook sound filetype:audio",
    },
    "pond_dordogne": {
        "titles": ["File:Nature sounds ambience in a Dordogne pond.ogg"],
        "search": "Dordogne pond filetype:audio",
    },
    "steam_train": {
        "titles": ["File:Train sounds from Iowa - Glaneur de sons.ogg"],
        "search": "Train sounds Glaneur de sons filetype:audio",
    },
    "steam_whistle": {
        "titles": ["File:WWS SteamWhistle.ogg", "File:Steam whistle blow.ogg"],
        "search": "SteamWhistle filetype:audio",
    },
    "river_waves": {
        "titles": ["File:Water wave.ogg"],
        "search": "Water wave filetype:audio",
    },
    "church_bells": {
        "titles": ["File:Samariter Church bell I (Es) 01.ogg", "File:Samariter Church Bell II (g).ogg"],
        "search": "Samariter Church bell filetype:audio",
    },
    "doves": {
        "titles": ["File:Columba livia - Rock Dove XC541143.mp3"],
        "search": "Columba livia Rock Dove filetype:audio",
    },
    "cicadas": {
        "titles": ["File:Cicada orni (Singing).ogg", "File:Cicada orni.ogg"],
        "search": "Cicada orni filetype:audio",
    },
    "wind_breeze": {
        "titles": ["File:Daniel Birch - 03 - Trees In The Wind.ogg", "File:Wind sounds 2020-05-10 1625.mp3"],
        "search": "Trees In The Wind filetype:audio",
    },
    "cafe_chatter": {
        "titles": ["File:Cafe ambiance.ogg"],
        "search": "Cafe ambiance filetype:audio",
    },
}

_HEADERS = {"User-Agent": "MonetCodePaintBot/4.0 (educational-art-project; github.com/yiggeror)"}


def _http_get_json(url, retries=5):
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            wait = 2.0 * (2 ** attempt)
            print(f"  [retry {attempt+1}/{retries}] API error {e}, sleeping {wait:.1f}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed Wikimedia API query: {url}")


def _resolve_all_urls():
    """Batch-resolve exact candidate File:... titles in minimal Wikimedia queries, then search fallback."""
    all_titles = []
    for cfg in SOURCES.values():
        all_titles.extend(cfg["titles"])

    title_to_info = {}
    # Query in chunks of 40 titles per request to respect API limits cleanly
    for i in range(0, len(all_titles), 40):
        chunk = "|".join(all_titles[i:i + 40])
        qs = urllib.parse.urlencode({
            "action": "query",
            "titles": chunk,
            "prop": "imageinfo",
            "iiprop": "url|mime|extmetadata",
            "format": "json",
        })
        data = _http_get_json(f"https://commons.wikimedia.org/w/api.php?{qs}")
        norm_map = {n["from"]: n["to"] for n in data.get("query", {}).get("normalized", [])}
        pages = data.get("query", {}).get("pages", {})
        for pg in pages.values():
            if "imageinfo" in pg:
                title_to_info[pg["title"]] = pg["imageinfo"][0]
        # map normalized back too
        for f_t, t_t in norm_map.items():
            if t_t in title_to_info:
                title_to_info[f_t] = title_to_info[t_t]
        time.sleep(0.8)

    resolved = {}
    for key, cfg in SOURCES.items():
        found = None
        for cand in cfg["titles"]:
            if cand in title_to_info:
                found = title_to_info[cand]
                break
        if found is None:
            # Search fallback in File namespace (ns=6)
            qs = urllib.parse.urlencode({
                "action": "query",
                "list": "search",
                "srnamespace": "6",
                "srsearch": cfg["search"],
                "srlimit": "5",
                "format": "json",
            })
            res = _http_get_json(f"https://commons.wikimedia.org/w/api.php?{qs}")
            hits = [h["title"] for h in res.get("query", {}).get("search", []) if h["title"].lower().endswith((".ogg", ".oga", ".mp3", ".wav", ".flac"))]
            if hits:
                qs2 = urllib.parse.urlencode({
                    "action": "query",
                    "titles": hits[0],
                    "prop": "imageinfo",
                    "iiprop": "url|mime|extmetadata",
                    "format": "json",
                })
                res2 = _http_get_json(f"https://commons.wikimedia.org/w/api.php?{qs2}")
                for pg in res2.get("query", {}).get("pages", {}).values():
                    if "imageinfo" in pg:
                        found = pg["imageinfo"][0]
                        break
            time.sleep(1.0)
        if found is None:
            raise RuntimeError(f"Could not resolve genuine Wikimedia audio source for '{key}'")
        resolved[key] = found
        print(f"  [resolved] {key}: {found['url']}")
    return resolved


def ensure_sources():
    os.makedirs(CACHE_DIR, exist_ok=True)
    meta_path = os.path.join(CACHE_DIR, "sources_meta.json")
    need_resolve = not os.path.exists(meta_path)
    if not need_resolve:
        with open(meta_path) as f:
            meta = json.load(f)
        if any(k not in meta for k in SOURCES):
            need_resolve = True
    if need_resolve:
        print("[audio] Resolving Wikimedia Commons genuine audio sources...")
        meta = _resolve_all_urls()
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    paths = {}
    for key, info in meta.items():
        if key not in SOURCES:
            continue
        url = info["url"]
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".ogg"
        local = os.path.join(CACHE_DIR, f"{key}{ext}")
        if not os.path.exists(local) or os.path.getsize(local) < 2000:
            for attempt in range(6):
                req = urllib.request.Request(url, headers=_HEADERS)
                try:
                    with urllib.request.urlopen(req, timeout=45) as r:
                        data = r.read()
                    with open(local, "wb") as f:
                        f.write(data)
                    print(f"  [downloaded] {key} ({len(data)//1024} KB)")
                    time.sleep(1.6)
                    break
                except Exception as e:
                    wait = 2.5 * (2 ** attempt)
                    print(f"  [download retry {attempt+1}/6] {key}: {e}, sleeping {wait:.1f}s")
                    time.sleep(wait)
            else:
                raise RuntimeError(f"Failed downloading {key} from {url}")
        paths[key] = local
    return paths


def _load_stereo(path, start_sec=0.0, dur_sec=None):
    cmd = ["ffmpeg", "-v", "error"]
    if start_sec > 0:
        cmd += ["-ss", f"{start_sec:.3f}"]
    cmd += ["-i", path]
    if dur_sec is not None:
        cmd += ["-t", f"{dur_sec:.3f}"]
    cmd += ["-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(SR), "pipe:1"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
    arr = np.frombuffer(res.stdout, dtype=np.float32).reshape(-1, 2).copy()
    peak = float(np.max(np.abs(arr))) + 1e-9
    rms = float(np.sqrt(np.mean(arr ** 2))) + 1e-9
    # Gentle normalization toward target RMS 0.14 without clipping
    gain = min(0.85 / peak, 0.14 / rms)
    return arr * gain


def _fade(arr, fade_in=0.5, fade_out=0.5):
    n = len(arr)
    fi = min(n // 2, int(round(fade_in * SR)))
    fo = min(n // 2, int(round(fade_out * SR)))
    out = arr.copy()
    if fi > 0:
        w = np.sin(np.linspace(0.0, np.pi * 0.5, fi, dtype=np.float32))[:, None]
        out[:fi] *= w
    if fo > 0:
        w = np.sin(np.linspace(np.pi * 0.5, 0.0, fo, dtype=np.float32))[:, None]
        out[-fo:] *= w
    return out


def _loop_fill(clip, target_sec):
    n_target = int(round(target_sec * SR))
    if len(clip) >= n_target:
        return clip[:n_target].copy()
    xf = min(len(clip) // 4, int(1.2 * SR))
    out = np.zeros((n_target, 2), np.float32)
    pos = 0
    while pos < n_target:
        rem = n_target - pos
        take = min(len(clip), rem)
        seg = clip[:take].copy()
        if pos > 0 and xf > 0 and take > xf:
            ramp = np.linspace(0.0, 1.0, xf, dtype=np.float32)[:, None]
            out[pos:pos + xf] = out[pos:pos + xf] * (1.0 - ramp) + seg[:xf] * ramp
            out[pos + xf:pos + take] = seg[xf:]
        else:
            out[pos:pos + take] = seg
        pos += take - (xf if pos + take < n_target else 0)
    return out


def _place(mix_buf, clip, t_start, gain=1.0, pan=0.0, fade_in=0.2, fade_out=0.3, lowpass_hz=None):
    arr = _fade(clip, fade_in=fade_in, fade_out=fade_out)
    if lowpass_hz is not None:
        sos = butter(3, lowpass_hz, btype="lowpass", fs=SR, output="sos")
        arr = sosfiltfilt(sos, arr, axis=0).astype(np.float32)
    # Equal-power stereo pan: pan in [-1 (L), +1 (R)]
    th = (np.clip(pan, -1.0, 1.0) + 1.0) * (np.pi * 0.25)
    gL = float(np.cos(th) * gain * 1.414)
    gR = float(np.sin(th) * gain * 1.414)
    s0 = int(round(t_start * SR))
    s1 = min(len(mix_buf), s0 + len(arr))
    if s1 <= s0 or s0 >= len(mix_buf):
        return
    a0 = max(0, -s0)
    s0 = max(0, s0)
    seg = arr[a0:a0 + (s1 - s0)]
    mix_buf[s0:s1, 0] += seg[:, 0] * gL
    mix_buf[s0:s1, 1] += seg[:, 1] * gR


def _place_moving_pan(mix_buf, clip, t_start, gain=1.0, pan0=-0.6, pan1=0.6, fade_in=0.3, fade_out=0.5, lowpass_hz=None):
    arr = _fade(clip, fade_in=fade_in, fade_out=fade_out)
    if lowpass_hz is not None:
        sos = butter(3, lowpass_hz, btype="lowpass", fs=SR, output="sos")
        arr = sosfiltfilt(sos, arr, axis=0).astype(np.float32)
    n = len(arr)
    pans = np.linspace(pan0, pan1, n, dtype=np.float32)
    th = (np.clip(pans, -1.0, 1.0) + 1.0) * (np.pi * 0.25)
    gL = np.cos(th) * gain * 1.414
    gR = np.sin(th) * gain * 1.414
    s0 = int(round(t_start * SR))
    s1 = min(len(mix_buf), s0 + n)
    if s1 > s0:
        mix_buf[s0:s1, 0] += arr[:s1 - s0, 0] * gL[:s1 - s0]
        mix_buf[s0:s1, 1] += arr[:s1 - s0, 1] * gR[:s1 - s0]


def build_master_wav(out_wav):
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    paths = ensure_sources()

    music = np.zeros((N_SAMPLES, 2), np.float32)
    sfx = np.zeros((N_SAMPLES, 2), np.float32)

    # 1. Three-movement genuine Classical Impressionist Suite (overlapping 3.5s velvet crossfades)
    # 0..42s: Debussy Arabesque No. 1 (sunlit poppy morning + Giverny lotus pond)
    arab = _load_stereo(paths["debussy_arabesque1"], start_sec=0.0, dur_sec=43.0)
    arab = _loop_fill(arab, 43.0)
    _place(music, arab, 0.0, gain=0.58, fade_in=1.5, fade_out=3.6)

    # 39..82s: Debussy La cathédrale engloutie (Seine mist viaduct + blazing Rouen sunset towers)
    cath = _load_stereo(paths["debussy_cathedrale"], start_sec=4.0, dur_sec=44.0)
    cath = _loop_fill(cath, 44.0)
    _place(music, cath, 38.5, gain=0.60, fade_in=3.6, fade_out=3.8)

    # 79..120s: Ravel Pavane pour une infante defunte (Provence lavender twilight + Venice night lagoon)
    pav = _load_stereo(paths["ravel_pavane"], start_sec=0.0, dur_sec=42.0)
    pav = _loop_fill(pav, 42.0)
    _place(music, pav, 78.5, gain=0.62, fade_in=3.8, fade_out=2.8)

    # 2. Scene-by-scene 100% Genuine Field Soundscape (with stereo spatial cues & warm distance filtering)
    # Scene 1 (0..20s): Skylark meadow, gentle wind, swallows, cheerful playful dog barks
    wind = _load_stereo(paths["wind_breeze"], dur_sec=22.0)
    _place(sfx, _loop_fill(wind, 21.0), 0.0, gain=0.14, pan=0.0, fade_in=1.5, fade_out=1.8, lowpass_hz=2800)
    sky_bird = _load_stereo(paths["skylark"], dur_sec=19.0)
    _place(sfx, _loop_fill(sky_bird, 18.0), 1.2, gain=0.22, pan=-0.25, fade_in=1.0, fade_out=1.5, lowpass_hz=7200)
    swal = _load_stereo(paths["swallow"], dur_sec=12.0)
    _place(sfx, swal, 8.0, gain=0.18, pan=0.45, fade_in=0.8, fade_out=1.2)
    dog = _load_stereo(paths["dog_bark"], dur_sec=2.8)
    _place(sfx, dog, 5.2, gain=0.18, pan=-0.15, fade_in=0.05, fade_out=0.2, lowpass_hz=4800)
    _place(sfx, dog, 12.8, gain=0.15, pan=0.18, fade_in=0.05, fade_out=0.2, lowpass_hz=4400)

    # Scene 2 (20..40s): Giverny babbling lotus brook & distant Dordogne pond frogs
    brook = _load_stereo(paths["brook"], dur_sec=21.0)
    _place(sfx, _loop_fill(brook, 21.0), 19.5, gain=0.24, pan=0.0, fade_in=1.6, fade_out=1.6, lowpass_hz=5200)
    pond = _load_stereo(paths["pond_dordogne"], dur_sec=19.0)
    _place(sfx, _loop_fill(pond, 19.0), 20.5, gain=0.17, pan=0.35, fade_in=1.5, fade_out=1.5, lowpass_hz=5600)

    # Scene 3 (40..60s): Seine water waves + Argenteuil promenade chatter + steam locomotive panning across bridge!
    waves = _load_stereo(paths["river_waves"], dur_sec=21.0)
    _place(sfx, _loop_fill(waves, 21.0), 39.5, gain=0.22, pan=0.0, fade_in=1.5, fade_out=1.6, lowpass_hz=4500)
    chatter = _load_stereo(paths["cafe_chatter"], dur_sec=18.0)
    _place(sfx, _loop_fill(chatter, 18.0), 40.5, gain=0.12, pan=0.45, fade_in=1.2, fade_out=1.4, lowpass_hz=3800)
    train = _load_stereo(paths["steam_train"], dur_sec=18.0)
    _place_moving_pan(sfx, _loop_fill(train, 18.0), 41.0, gain=0.30, pan0=-0.75, pan1=0.75, fade_in=1.5, fade_out=1.8, lowpass_hz=5200)
    whistle = _load_stereo(paths["steam_whistle"], dur_sec=2.6)
    _place(sfx, whistle, 47.0, gain=0.20, pan=-0.20, fade_in=0.15, fade_out=0.5, lowpass_hz=4200)
    _place(sfx, whistle, 53.0, gain=0.15, pan=0.38, fade_in=0.15, fade_out=0.6, lowpass_hz=3600)

    # Scene 4 (60..80s): Rouen cathedral golden evening church bells + fluttering plaza doves + soft evening ambiance
    bells = _load_stereo(paths["church_bells"], dur_sec=18.0)
    _place(sfx, _loop_fill(bells, 17.5), 60.5, gain=0.26, pan=0.0, fade_in=1.5, fade_out=2.2, lowpass_hz=5000)
    dove = _load_stereo(paths["doves"], dur_sec=14.0)
    _place(sfx, _loop_fill(dove, 14.0), 63.0, gain=0.20, pan=-0.35, fade_in=1.0, fade_out=1.5, lowpass_hz=6400)
    _place(sfx, _loop_fill(chatter, 16.0), 61.5, gain=0.10, pan=0.30, fade_in=1.5, fade_out=1.5, lowpass_hz=3200)

    # Scene 5 (80..100s): Provence summer dusk cicadas + warm twilight breeze across lavender hills
    cic = _load_stereo(paths["cicadas"], dur_sec=20.0)
    _place(sfx, _loop_fill(cic, 20.0), 80.0, gain=0.21, pan=-0.25, fade_in=1.6, fade_out=1.8, lowpass_hz=7600)
    _place(sfx, _loop_fill(wind, 20.0), 80.0, gain=0.16, pan=0.20, fade_in=1.6, fade_out=1.8, lowpass_hz=2600)

    # Scene 6 (100..120s): Venice twilight lagoon waves + gentle night breeze + distant nocturnal sanctuary bell
    _place(sfx, _loop_fill(waves, 20.0), 100.0, gain=0.22, pan=0.0, fade_in=1.6, fade_out=2.6, lowpass_hz=3600)
    _place(sfx, _loop_fill(bells, 10.0), 106.0, gain=0.14, pan=0.35, fade_in=1.8, fade_out=2.6, lowpass_hz=2800)

    # Duck music slightly beneath resonant bell/whistle/train swells cleanly, blend & soft-limit
    sfx_env = np.convolve(np.abs(sfx).mean(axis=1), np.ones(int(0.4 * SR), np.float32) / int(0.4 * SR), mode="same")
    duck = np.clip(1.0 - 0.35 * sfx_env, 0.78, 1.0)[:, None]
    master = music * duck + sfx

    # Gentle stereo limiting so zero sample clips (> -1.0 dBFS ceiling = 0.891)
    peak = float(np.max(np.abs(master)))
    if peak > 0.89:
        master = np.tanh(master * (0.95 / peak)) * 0.891
    else:
        rms = float(np.sqrt(np.mean(master ** 2))) + 1e-9
        gain = min(0.891 / peak, 0.165 / rms)
        master *= gain

    # Write 24-bit WAV cleanly via ffmpeg raw float32 pipe
    cmd = [
        "ffmpeg", "-y",
        "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(SR),
        "-i", "pipe:0",
        "-c:a", "pcm_s24le",
        out_wav,
    ]
    subprocess.run(cmd, input=master.astype(np.float32).tobytes(), check=True)
    print(f"[audio] Master 24-bit 48kHz stereo WAV written -> {out_wav} ({DUR:.1f}s)")


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "output/master_v4_120s.wav"
    build_master_wav(out)
