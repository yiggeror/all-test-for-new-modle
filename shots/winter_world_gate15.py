# Derived from Rainroji d3fff8c, film/scenes/snow.py. Kept separate from the unmodified baseline.
"""冬 · 雪 · 蓝调时刻 —— 家属院 (worker housing compound, winter dusk, snow)"""
import numpy as np
from engine.world import World, srgb, MASK_THIN, MASK_NOSHADOW
from engine.render import Camera
from engine import props as pr, mats, fx
from engine.mats import mat, sstep, mix
from engine.noise import fbm2, hash2
from engine.hooks import snow_hook, GroundMap

NAME = 'snow'; T = 9.0; K = 8          # groups: 0 static, 1 sodium lamp, 2 TV window, 3..7 stairwell lights (sound-activated, climbing)
G_LAMP, G_TV, G_ST = 1, 2, 3
SODIUM = '#ff9a3c'

def sky(d):
    y = np.clip(d[:, 1], -0.2, 1)
    zen = srgb('#2f4264') * 0.50; hor = srgb('#7189ab') * 0.60
    t = np.clip(y, 0, 1) ** 0.55
    c = hor[None] * (1 - t[:, None]) + zen[None] * t[:, None]
    az = np.arctan2(d[:, 0], -d[:, 2])
    glow = np.exp(-((az + 0.9) / 0.8) ** 2) * np.exp(-np.clip(y, 0, 1) * 6)
    c = c + glow[:, None] * srgb('#b08f8a')[None] * 0.10
    cl = fbm2(az * 2.2, y * 9.0, 8, 4)
    c = c * (0.86 + 0.28 * cl)[:, None]
    return c.astype(np.float32)

FOG = dict(sigma=0.0034, color=lambda d: sky(np.stack([d[:, 0], np.maximum(d[:, 1], 0.02), d[:, 2]], 1)) * 0.95)

TREES = [(-8.0, 12.4, 17.2), (-4.9, -6.9, 15), (-1.5, -11, 16), (1.0, -10.2, 14),
         (0.0, -18, 16), (-6.9, -18.6, 15), (-0.65, -26.8, 15), (1.0, -29, 14),
         (9.25, -12.6, 12.5), (-6.5, -15, 14), (13.5, -13, 13), (15.0, 2, 14)]
GUARD_POS = (5.34, 0.0, -11.1)
GUARD_YAW = -.19
GUARD_SIZE = (4.35, 2.92, 2.91)
READING_OPENING = (.44, .86, 2.49, 2.34)


def reading_room_window(w, width, height):
    """Static reading pose inside the opening, not a post-composited face or a motion preview."""
    light = dict(mat='emit', col='#e6a158', prm=(.56, 0, 0, 0), tag=pr.TAG_NOSNOW)
    w.quads((-.25, -.16, -.64), (width + .22, -.16, -.64),
            (width + .22, height + .20, -.64), (-.25, height + .2, -.64), **light)
    w.quads((0, .01, -.61), (width, .01, -.61), (width, .25, -.61), (0, .25, -.61),
            mat='emit', col='#985e38', prm=(.47, 0, 0, 0), tag=pr.TAG_NOSNOW)
    shadow = dict(mat='plain', col='#453235', tag=pr.TAG_NOSNOW)
    sleeve = dict(mat='plain', col='#5c4039', tag=pr.TAG_NOSNOW)
    # Reading at the desk: rounded back, a bent neck, forearm down and book open.
    w.sphere((.63, .39, -.27), .23, n=10, squash=1.45, **shadow)
    w.tube((.69, .51, -.25), (.82, .76, -.23), .13, .10, sides=8, caps=True, **shadow)
    w.sphere((.87, .83, -.21), .132, n=10, squash=1.03, **shadow)
    w.sphere((.96, .79, -.22), .052, n=7, squash=.62, **shadow)
    w.box((1.12, .26, -.18), (1.20, .105, .28), mat='wood', col='#714938', tag=pr.TAG_NOSNOW)
    w.tube((.73, .57, -.13), (.91, .36, -.04), .08, .064, sides=7, caps=True, **sleeve)
    w.tube((.91, .36, -.04), (1.19, .34, -.02), .06, .041, sides=7, caps=True, **sleeve)
    for x in (1.18, 1.39):
        w.box((x, .325, -.035), (.195, .026, .17), yaw=.13, mat='emit',
              col='#ddc49d', prm=(.35, 0, 0, 0), tag=pr.TAG_NOSNOW)
    # Lamp is recognizably inside: shade, thin stem, warm halo on the wall.
    w.tube((1.69, .30, -.26), (1.67, .71, -.28), .021, sides=6, **shadow)
    w.tube((1.67, .74, -.28), (1.67, .965, -.28), .20, .081, sides=10, caps=True,
           mat='emit', col='#ffd6a0', prm=(.81, 0, 0, 0), tag=pr.TAG_NOSNOW)
    w.light('point', np.asarray(srgb('#ffd396')) * .70, pos=(1.62, .73, -.32),
            radius=.07, range=1.45, r0=.24, grp=0)
    for x in (.025, width - .024):
        w.box((x, height / 2, .02), (.09, height, .08), mat='wood', col='#483a37', tag=pr.TAG_NOSNOW)
    for y in (.029, height - .021):
        w.box((width / 2, y, .02), (width, .072, .093), mat='wood', col='#483a37', tag=pr.TAG_NOSNOW)
    w.box((width / 2, height - .19, .02), (width, .057, .068), mat='wood', col='#58423a', tag=pr.TAG_NOSNOW)


def courtyard_guard_room(w):
    width, depth, height = GUARD_SIZE
    wall = dict(mat='plaster', col='#8a8b87')
    def door(w_, ww, hh):
        w_.box((ww/2, hh/2, 0), (ww, hh, .096), mat='wood', col='#555851')
        w_.box((.21, 1.03, .054), (.045,.04,.018), mat='metal', col='#8d745a')
    with w.at((-width/2, 0, depth/2)):
        pr.wall(w, width, height, [(*READING_OPENING, reading_room_window, .16),
                                  (2.98, 0, 4.02, 2.18, door, .11)], **wall)
        pr.sill(w, READING_OPENING[0], READING_OPENING[1], READING_OPENING[2], out=.19, th=.09, col='#ccc3b2')
        w.box((3.50, .095, .27), (1.25, .19, .63), mat='concrete', col='#99968b')
        w.box((3.51, 2.54, .016), (.65, .24, .043), mat='wood', col='#765a49')
    w.box((0, height/2, -.013), (width, height, depth-.026), mat='plaster', col='#767e83', faces='xXz')
    w.box((0, .17, .002), (width+.03, .34, depth+.012), mat='brick', col='#706458', faces='xXzZ')
    w.box((0, height+.065, .05), (width+.42,.14,depth+.51), mat='concrete', col='#7c8386')
    w.box((0, height+.165, .08), (width+.40,.11,depth+.53), mat='snow', col='#e2eaf1')
    w.tube((1.23, height+.13, -.90), (1.23, height+.76, -.90), .085, sides=7,
           mat='metal', col='#54545a', caps=True)
    w.light('point', np.asarray(srgb('#fbb36d')) * 1.7, pos=(-.65, 1.48, depth/2+.22),
            axis=(0,-.67,1), cone=(.04,.75), radius=.22, range=8.0, r0=.75)

def build():
    w = World(seed=7); rng = np.random.default_rng(11)
    # ------------------------------------------------ ground with paths
    gm = GroundMap(-80, -120, 80, 60, res=12)
    lane = [(-10.5, 60), (-10.5, 20), (-10.3, -10), (-10.8, -60), (-10.5, -120)]
    gm.line(lane, 3.4, 0.55)
    for dx in (-0.8, 0.8):                                  # tyre tracks
        gm.line([(p[0] + dx, p[1]) for p in lane], 0.35, 1.0)
    gm.line([(-9, 3), (-3, 2), (4, -4), (10, -12), (14, -16)], 0.7, 0.8)      # footpath across the yard
    gm.line([(4, -4), (3, -14), (4, -30)], 0.6, 0.7)
    gm.line([(-10.6, 9), (-10.9, 1.4)], 0.3, 0.9)
    gm.line([(4, -30), (14, -40), (30, -46), (60, -58)], 2.6, 0.6)                         # drive in front of block B1
    gm.line([(14, -16), (17, -4), (24, 10), (27, 40)], 2.2, 0.5)
    for k in range(40):                                       # scattered footprints / scuffs
        c = (rng.uniform(-20, 30), rng.uniform(-40, 25)); gm.disc(c, rng.uniform(0.15, 0.5), rng.uniform(0.2, 0.6))
    frng = np.random.default_rng(77)
    trails = [[(19.4, 2.0), (12, -1), (5.5, -3.5), (-2, 0.5), (-8.6, 3.0)], [(19.4, -11.0), (11, -15), (4, -13), (-6.6, -22.5)], [(19.4, 15.0), (14, 10), (8, 9.5)],
              [(0.8, -4.2), (2.6, -9), (2.0, -13.5), (6, -22), (10, -36)], [(-8.8, -24.5), (-9.6, -18), (-10.4, -8)], [(-13.5, 12), (-12.6, 2), (-13.0, -12), (-12.8, -22)],
              [(1.5, -3.0), (4.5, -2.4), (3.4, 0.2), (0.6, -2.2), (2.2, -5.6)], [(-3, -8), (0, -17), (-4, -26), (-3, -40)], [(8, -12), (15, -24), (24, -44)]]
    for tr in trails:
        gm.steps(tr, stride=0.66, r=0.12, v=0.95); gm.steps([(p[0] + frng.normal(0, 0.25), p[1] + frng.normal(0, 0.25)) for p in tr[::-1]], stride=0.7, r=0.12, v=0.8)
    for c in ((0.8, -4.2), (3.6, -2.0), (2.0, -13.5)):
        for k in range(26): gm.disc((c[0] + frng.normal(0, 0.9), c[1] + frng.normal(0, 0.9)), 0.13, 0.85)
    gm.done(blur=0.045)
    rm = GroundMap(-80, -120, 80, 60, res=6)                 # ridges / drifts
    for dx in (-2.5, 2.6):
        rm.line([(p[0] + dx, p[1]) for p in lane], 0.9, 1.0)
    rm.line([(-14.6, 26), (-14.6, -23)], 1.0, 0.8)
    rm.line([(4, -34), (18, -44), (40, -52)], 1.2, 0.7); rm.line([(18.2, 20), (18.2, -22)], 1.3, 0.9)
    for (x, z, r_) in TREES: rm.disc((x, z), 0.9, 0.5)
    for k in range(60): rm.disc((rng.uniform(-30, 30), rng.uniform(-60, 25)), rng.uniform(0.5, 1.6), rng.uniform(0.2, 0.6))
    rm.done(blur=0.5)
    def height(x, z):
        h = 0.16 * (fbm2(x * 0.11, z * 0.11, 3, 3) - 0.5) + 0.05 * (fbm2(x * 0.6, z * 0.6, 5, 3) - 0.5)
        return h - 0.085 * gm.sample(x, z) + 0.30 * rm.sample(x, z)
    @mat('gsnow')
    def gsnow(S):
        x, z = S.P[:, 0], S.P[:, 2]
        tr = gm.sample(x, z)
        n1 = fbm2(x * 0.25, z * 0.25, 3, 4); n2 = fbm2(x * 4, z * 4, 9, 3); n3 = fbm2(x * 1.1, z * 1.1, 19, 3)
        base = 0.82 + 0.14 * n1 + 0.10 * (n2 - 0.5) * mats.fade(S, 4) + 0.08 * (n3 - 0.5)
        trn = np.clip(tr * (0.75 + 0.5 * (n3 - 0.5)), 0, 1)
        alb = srgb('#e2e9f1')[None] * base[:, None]
        packed = srgb('#9aa1a8')[None] * (0.75 + 0.5 * n3)[:, None]
        e = 0.12
        bump = lambda xx, zz: height(xx, zz) + 0.012 * fbm2(xx * 2.5, zz * 2.5, 41, 2)
        gx = (bump(x + e, z) - bump(x - e, z)) / (2 * e); gz = (bump(x, z + e) - bump(x, z - e)) / (2 * e)
        N = np.stack([-gx, np.ones_like(gx), -gz], 1); N /= np.linalg.norm(N, axis=1, keepdims=True)
        return dict(alb=np.clip(mix(alb, packed, trn * 0.7), 0, 1), N=N.astype(np.float32))
    w.grid(-34, -64, 34, 26, 0.3, height, mat='gsnow', tag=pr.TAG_NOSNOW, seed=0.5)
    w.quads((-300, -0.03, 150), (300, -0.03, 150), (300, -0.03, -400), (-300, -0.03, -400), mat='gsnow', tag=pr.TAG_NOSNOW)

    def lit_fn_none(*a): return None
    # ------------------------------------------------ hero block B1 (mid right)
    def b1_lit(side, u, b, f):
        if side == 'front' and (u, b, f) == (0, 1, 2): return (1.32, '#ffd093', 0)
        if side == 'front' and (u, b, f) == (1, 2, 2): return (0.92, '#ffc486', 0)
        if side == 'front' and (u, b, f) == (1, 2, 1): return (0.9, '#9fb4d8', G_TV)
        if side == 'front' and (u, b, f) == (2, 1, 4): return (1.1, '#ffd08a', 0)
        if side == 'front' and (u, b, f) == (1, 1, 5): return (0.8, '#ffb45e', 0)
        if side == 'balc' and (u, b, f) == (0, 3, 2): return (0.9, '#f5c98a', 0)
        return (0.0, '#ffc070', 0)
    with w.at((14, 0, -49), yaw=0.42):
        info = pr.apt_block(w, units=3, floors=6, style='brick', rng=np.random.default_rng(3), grp_fn=b1_lit, cages=0.2, ac=0.04)
        with w.at((-info['W'] / 2, 0, -info['D'] / 2), yaw=-np.pi / 2):          # left gable: whitewashed panel with a painted slogan
            pr.wall_text(w, '讲文明树新风', 4.3, 16.6, size=1.55)
    # ------------------------------------------------ near right block B2 (cropped by the frame)
    def b2_lit(side, u, b, f):
        if side == 'stair' and u == 0: return (1.5, '#ffcf8f', G_ST + min(f, 4)) if f < 5 else (0.0, '#ffc070', 0)
        if side == 'stair': return (0.0, '#ffc070', 0)
        return None
    with w.at((25.3, 0, 0), yaw=np.pi / 2 - 0.02):
        pr.apt_block(w, units=3, floors=7, style='tile', rng=np.random.default_rng(5), lit=0.035, cages=0.25, ac=0.06, grp_fn=b2_lit, couplets=True)
    # ------------------------------------------------ near left block B3
    with w.at((-27.3, 0, -20), yaw=np.pi / 2 + 0.03):
        pr.apt_block(w, units=3, floors=6, style='brick2', rng=np.random.default_rng(8), lit=0.07, cages=0.2)
    # ------------------------------------------------ far blocks
    far = [((-58, 0, -88), 0.1, 3, 5, 'plaster'), ((-6, 0, -104), -0.05, 4, 6, 'brick'), ((66, 0, -96), 0.2, 3, 6, 'yellow'),
           ((-70, 0, -140), 0.0, 4, 6, 'brick2'), ((10, 0, -150), 0.1, 5, 6, 'plaster'), ((90, 0, -150), -0.1, 4, 7, 'tile'),
           ((-28, 0, -200), 0.0, 5, 6, 'brick'), ((60, 0, -215), 0.05, 5, 6, 'plaster')]
    for i, (p, yw, un, fl, stl) in enumerate(far):
        with w.at(p, yaw=yw):
            pr.apt_block(w, units=un, floors=fl, style=stl, rng=np.random.default_rng(20 + i), lit=0.07, details=False, cages=0, roof_stuff=(i < 3), lit_gain=1.2)
    # water tower + boiler chimney
    w.tube((-22, 0, -118), (-22, 22, -118), 1.6, 1.3, sides=10, mat='brick', col='#7c5448')
    w.tube((-22, 22, -118), (-22, 27, -118), 3.4, 3.4, sides=12, mat='plaster', col='#8f8c84', caps=True)
    w.tube((36, 0, -170), (36, 52, -170), 2.3, 1.2, sides=10, mat='brick', col='#7c5448')
    w.box((48, 5, -168), (26, 10, 14), mat='brick', col='#7c5448')
    # ------------------------------------------------ sheds along the lane
    with w.at((-15.6, 0, 26), yaw=np.pi / 2):
        pr.shed_row(w, n=19, rng=np.random.default_rng(2))
    with w.at((-6.0, 0, -39.0), yaw=-np.pi / 2):
        pr.shed_row(w, n=6, depth=2.8, rng=np.random.default_rng(4), style='plaster')
    # ------------------------------------------------ lamp + poles + wires
    pts, lamp = pr.pole(w, (-7.75, 0, 5.5), h=9.2, lamp=dict(dir=(-1, 0.1), color='#ffa85c', grp=G_LAMP, power=23.0, h=7.3, arm=1.7, vol=0.0058, cone=(0.22, 0.84)))
    pts2, _ = pr.pole(w, (-7.6, 0, -36), h=9.0)
    pts3, _ = pr.pole(w, (-8.2, 0, 44), h=9.0)
    pts4, _ = pr.pole(w, (9, 0, -16), h=8.5, arms=1)
    for a, b in zip(pts, pts2): pr.wire(w, a, b, sag=0.9)
    for a, b in zip(pts, pts3): pr.wire(w, a, b, sag=0.9)
    for a, b in zip(pts[:4], pts4): pr.wire(w, a, b, sag=0.7)
    pr.wire(w, pts4[1], (6, 12.5, -33), sag=0.4); pr.wire(w, pts[0], (-22, 10.0, -6), sag=0.5); pr.wire(w, pts4[2], (20, 13.0, -6), sag=0.5)
    # ------------------------------------------------ trees
    trng = np.random.default_rng(42)
    for i, (x, z, h) in enumerate(TREES):
        pr.tree(w, (x, 0, z), h, 'poplar', trng, trunk_r=0.21 if i == 0 else None,
                detail=.94 if i == 0 else (1.09 if i < 6 else 1.0), maxd=6 if i < 4 else None)
    for i in range(26):                                   # far tree belt
        pr.tree(w, (trng.uniform(-62, 6), 0, trng.uniform(-100, -74)), trng.uniform(11, 16), 'poplar' if trng.random() < 0.7 else 'elm', trng, detail=0.75)
    for i in range(8):
        pr.tree(w, (trng.uniform(40, 75), 0, trng.uniform(-84, -66)), trng.uniform(10, 14), 'elm', trng, detail=0.7)
    # ------------------------------------------------ cars, table, bikes, courtyard guard-room
    with w.at((13.0, 0, -42.5), yaw=0.6): pr.car(w, 'van', '#b9bcc0')
    with w.at((19.0, 0, -45.5), yaw=0.4): pr.car(w, 'sedan', '#5a2a26')
    with w.at((3.6, 0, -2.0), yaw=0.3): pr.pingpong(w)
    for i, (z, yw) in enumerate([(9.5, 0.2), (8.6, 0.1), (-3.0, -0.2), (-15.5, 0.15)]):
        with w.at((-14.8, 0, z), yaw=np.pi / 2 + yw): pr.bicycle(w, lean=0.2)
    with w.at(GUARD_POS, yaw=GUARD_YAW):
        courtyard_guard_room(w)
    pr.pole(w, (-14.3, 0, -13.5), h=6.6, arms=0, col='#6a6660')
    pr.banner(w, (-14.3, 6.3, -13.5), (-6.5, 6.1, -15.0), '欢度春节', h=1.0, sag=0.15)
    with w.at((-15.6, 0, 26), yaw=np.pi / 2):                                        # 福 squares on a few shed doors
        for i in (5, 8, 9, 12, 14):
            w.box((i * 2.6 + 1.3 + np.random.default_rng(i).uniform(-0.25, 0.25), 1.35, 0.06), (0.32, 0.32, 0.01), mat='plain', col='#a82a22', tag=pr.TAG_NOSNOW)
    with w.at((2.0, 0, -13.5), yaw=0.5): pr.drying_frame(w)
    with w.at((0.65, 0.025, 2.40), yaw=-1.35, scale=1.12):
        pr.snowman(w)
        w.tube((0, 1.135, 0), (0, 1.22, 0), 0.235, 0.21, sides=9, caps=True,
               mat='plain', col='#a14c3c', tag=pr.TAG_NOSNOW)
        for z_eye in (-0.066, 0.066):
            w.sphere((0.182, 1.422, z_eye), 0.033, n=6, mat='plain', col='#252532', tag=pr.TAG_NOSNOW)
    with w.at((-7.0, 0, -9.0), yaw=-np.pi / 2): pr.notice_board(w)
    pr.heat_pipes(w, [(17.6, 24), (17.6, -8), (17.6, -21)])
    crng = np.random.default_rng(55)
    pr.hedge(w, (-6.9, 0, -1.0), (-7.2, 0, -7.0), rng=crng); pr.hedge(w, (-7.2, 0, -11.0), (-7.4, 0, -21.0), rng=crng)
    pr.hedge(w, (12.2, 0, 6.0), (12.4, 0, -6.0), rng=crng); pr.hedge(w, (11.0, 0, -22.0), (3.0, 0, -31.0), rng=crng)
    for k in range(16): pr.shrub(w, (crng.uniform(-6, 14), 0, crng.uniform(-34, 4)), r=crng.uniform(0.4, 0.9), h=crng.uniform(0.7, 1.5), rng=crng)
    with w.at((3.94, 0.02, 0.70), yaw=0.22):
        w.box((0, 0.48, 0), (2.30, 0.20, 0.61), mat='concrete', col='#a8a59c')
        for x in (-0.78, 0.78):
            w.box((x, 0.19, 0), (0.33, 0.38, 0.45), mat='concrete', col='#838590')
    for (x, z, yw) in ((8.8, -17.0, 0.6),):
        with w.at((x, 0, z), yaw=yw): pr.bench(w)
    with w.at((18.4, 0, 4.5), yaw=0.0): pr.bike_row(w, 7, rng=crng)
    with w.at((18.6, 0, -8.5), yaw=0.0): pr.bike_row(w, 5, rng=crng)
    with w.at((-5.4, 0, -22.4), yaw=np.pi / 2): pr.bike_row(w, 3, rng=crng)
    for (x, z) in ((-13.3, 14.0), (-13.4, -6.0), (-13.2, -17.5), (16.6, 9.0), (7.5, -40.5)):
        with w.at((x, 0, z)): pr.junk_pile(w, crng)
    with w.at((14.8, 0, -3.0), yaw=0.2): pr.trike(w)
    pr.mound(w, (-13.2, 0, 1.5), 1.3, 0.8); pr.mound(w, (-13.0, 0, -11.0), 1.0, 0.6, col='#2a2622')
    return w

def camera():
    return Camera((0.5, 13.5, 38.0), (1.0, 6.7, -8.0), fov=58.0)

HOOK = snow_hook(shelter=1.5)
RENDER = dict(K=K, fog=FOG, hook=HOOK, bounce_range=70.0, skyamb=1.35)
GRADE = dict(exposure=3.0, contrast=1.22, sat=1.0, shoulder=1.0, lift=(0.02, 0.025, 0.04))
PAL = dict(k=88, chroma_w=3.0, extra=[(0.78, 0.82, 0.88), (0.62, 0.68, 0.78)])

# ------------------------------------------------------------------ animation
CHIMNEY_TOP = (36, 52.5, -170)

def setup(plate, cam):
    c = dict(plate=plate, cam=cam)
    H, W = plate['sky'].shape
    import sys
    c['sky'] = fx.native_sky(sys.modules[__name__], cam, H, W) * plate['sky'][..., None]
    c['lamp'] = [L for L in plate['lights'] if L['grp'] == G_LAMP][0]
    amb = sky(np.array([[0.2, 0.8, 0.1], [-0.4, 0.5, 0.3], [0.1, 0.3, -0.8]], np.float32)).mean(0)
    c['amb'] = (amb * 0.3 + amb.mean() * 0.7) * 2.1
    c['snow'] = [fx.Particles(cam, plate, n=6400, T=T, seed=1, near=30, far=150, vel=(0.25, -0.9, 0.05), size=0.05, dpow=1.0, sway=0.25),
                 fx.Particles(cam, plate, n=1850, T=T, seed=2, near=9, far=40, vel=(0.35, -1.1, 0.1), size=0.035, dpow=0.6, sway=0.2),
                 fx.Particles(cam, plate, n=82, T=T, seed=3, near=1.5, far=9, vel=(0.4, -1.2, 0.1), size=0.022, dpow=0.5, sway=0.12, loops=2)]
    c['smoke'] = [fx.Smoke(cam, plate, CHIMNEY_TOP, n=14, T=T, loops=1, rise=1.6, wind=(1.6, 0, 0.3), r0=1.6, grow=1.1, seed=5, alpha=0.5)]
    c['lamp_px'] = cam.project(np.array([c['lamp']['pos']]) + np.array([[0, 0.15, 0]]))
    c['chim_px'] = cam.project(np.array([CHIMNEY_TOP]))
    return c

def gains(ph):
    g = np.ones(K, np.float32)
    g[G_LAMP] = 1.0 + 0.05 * (fx.loopnoise(ph, 24, 3) - 0.5) - 0.22 * fx.pulse(ph, 0.615, 0.635, 0.006)
    for k in range(5):                          # someone climbs the stairs: each landing lights for ~2 s
        t0 = (0.6 + 1.2 * k) / T
        g[G_ST + k] = fx.pulse(ph, t0, t0 + 2.0 / T, 0.004)
    return g

def frame(c, ph):
    L = c['plate']['layers']; g = gains(ph)
    lin = c['sky'].copy()
    for k in range(K):
        if k == G_TV: continue
        lin += g[k] * L[k]
    tv = 0.45 + 0.9 * fx.stepnoise(ph, 34, 11) * (0.6 + 0.4 * fx.stepnoise(ph, 9, 12))
    tint = np.array([0.8, 0.95, 1.25]) * (1 - fx.stepnoise(ph, 13, 14) * 0.5) + np.array([1.2, 1.0, 0.7]) * fx.stepnoise(ph, 13, 14) * 0.5
    lin += L[G_TV] * (tv * tint)[None, None]
    amb = c['amb']
    for s in c['smoke']:
        s.draw(lin, ph, amb * 0.55)
    lamp = c['lamp']
    ll = [(lamp['pos'], lamp['color'] * g[G_LAMP] * 0.5, 0.8, lamp['axis'], lamp['cone'])]
    c['snow'][0].draw(lin, ph, amb, ll, alpha=0.55)
    c['snow'][1].draw(lin, ph, amb, ll, alpha=0.65)
    c['snow'][2].draw(lin, ph, amb * 1.1, ll, alpha=0.73)
    x, y, _, _ = c['lamp_px']
    fx.glow(lin, x[0], y[0], lamp['color'] * 0.012 * g[G_LAMP], r0=2.2, power=1.3)
    blink = fx.pulse(ph, 0.02, 0.10, 0.02) + fx.pulse(ph, 0.52, 0.60, 0.02)
    x, y, _, _ = c['chim_px']
    fx.glow(lin, x[0], y[0] - 0.5, np.array([1.0, 0.08, 0.05]) * 0.6 * blink, r0=0.7, power=2.0)
    return fx.bloom(lin, thresh=0.55, sig=(1.0, 3.5), gain=(0.22, 0.14))
