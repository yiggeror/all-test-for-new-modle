"""Assemble the five continuous Impressionist scenes and living actors."""
import numpy as np
import sky_atmo
import s1_etretat
import s2_argenteuil
import s3_giverny
import s4_rouen
import s5_venice
import life

SETS = []
ACTORS = []


def _init():
    rng = np.random.default_rng(2026)
    for mod in (sky_atmo, s1_etretat, s2_argenteuil, s3_giverny, s4_rouen, s5_venice, life):
        s, a = mod.build(rng)
        SETS.extend(s)
        ACTORS.extend(a)


_init()
