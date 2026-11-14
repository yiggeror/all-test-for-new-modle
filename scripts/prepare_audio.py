#!/usr/bin/env python3
"""
Builds the 92.0-second stereo master soundtrack for 'Un Jour à Giverny':
- Debussy: Clair de Lune (209.3s -> 301.3s, natural reprise to final resolving chord)
- Scene-synced ambient nature SFX crossfaded seamlessly across all 5 scenes
"""
import os
import subprocess

ROOT = os.getcwd()
AUDIO_DIR = os.path.join(ROOT, "assets", "audio")
OUT_WAV = os.path.join(AUDIO_DIR, "master_92s.wav")

DURATION = 92.0

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    clair = os.path.join(AUDIO_DIR, "clair_de_lune.ogg")
    waves = os.path.join(AUDIO_DIR, "shore_waves.mp3")
    breeze = os.path.join(AUDIO_DIR, "breeze_birds.ogg")
    creek = os.path.join(AUDIO_DIR, "creek_forest.ogg")
    birds = os.path.join(AUDIO_DIR, "summer_birds.mp3")
    bees = os.path.join(AUDIO_DIR, "crickets_bees.mp3")
    night = os.path.join(AUDIO_DIR, "night_crickets.ogg")

    # Complex FFmpeg filtergraph mixing music + 5 scene-synced nature SFX layers
    filter_complex = (
        # Music: slice 209.3s..301.3s (92s), resample 48k stereo, gentle fade in/out, slight warm boost
        "[0:a]atrim=start=209.3:duration=92.0,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,"
        "volume=1.35,afade=t=in:st=0:d=2.2,afade=t=out:st=89.0:d=3.0[music];"

        # Scene 1 (0..21s): Gentle shore lapping + early dawn birds
        "[1:a]aloop=loop=2:size=2680000,atrim=0:22,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,lowpass=f=2400,"
        "volume=0.22,afade=t=in:st=0:d=2.0,afade=t=out:st=17:d=5.0[s1_waves];"

        "[2:a]atrim=0:22,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=350,"
        "volume=0.14,afade=t=in:st=1.0:d=3.0,afade=t=out:st=17:d=5.0[s1_birds];"

        # Scene 2 (16..40s): Giverny garden creek + cheerful morning birds
        "[3:a]atrim=start=15:duration=25,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,lowpass=f=3500,"
        "volume=0.16,afade=t=in:st=0:d=4.0,afade=t=out:st=20:d=5.0,adelay=16000|16000[s2_creek];"

        "[4:a]atrim=start=10:duration=42,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=450,"
        "volume=0.16,afade=t=in:st=0:d=4.0,afade=t=out:st=36:d=6.0,adelay=17000|17000[s23_birds];"

        # Scene 3-4 (42..76s): Summer meadow bees & warm afternoon insects
        "[5:a]atrim=start=0:duration=35,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=300,"
        "volume=0.20,afade=t=in:st=0:d=5.0,afade=t=out:st=29:d=6.0,adelay=41000|41000[s34_bees];"

        # Scene 5 (71..92s): Twilight crickets + calm night water ripples
        "[6:a]aloop=loop=2:size=1600000,atrim=0:22,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=500,lowpass=f=6500,"
        "volume=0.16,afade=t=in:st=0:d=4.5,afade=t=out:st=18.5:d=3.5,adelay=70000|70000[s5_night];"

        "[1:a]atrim=start=10:duration=22,asetpts=PTS-STARTPTS,"
        "aformat=sample_rates=48000:channel_layouts=stereo,lowpass=f=1800,"
        "volume=0.16,afade=t=in:st=0:d=4.0,afade=t=out:st=18.5:d=3.5,adelay=70000|70000[s5_waves];"

        # Combine all layers cleanly & apply gentle loudness normalization
        "[music][s1_waves][s1_birds][s2_creek][s23_birds][s34_bees][s5_night][s5_waves]"
        "amix=inputs=8:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.92,atrim=0:92.0[out]"
    )

    run([
        "ffmpeg", "-y",
        "-i", clair,
        "-i", waves,
        "-i", breeze,
        "-i", creek,
        "-i", birds,
        "-i", bees,
        "-i", night,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
        OUT_WAV,
    ])

    # Verify duration & volume of master_92s.wav
    run(["ffmpeg", "-i", OUT_WAV, "-af", "volumedetect", "-f", "null", "-"])
    print("Master audio ready:", OUT_WAV)

if __name__ == "__main__":
    main()
