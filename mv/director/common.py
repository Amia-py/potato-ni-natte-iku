"""Shared director utilities: audio clock, easing, stateless emitters (potatoes / particles)."""
import json, math, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/')
WORK = f'{ROOT}/work'


# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def ease_out(t, p=3): t = clamp(t); return 1 - (1 - t) ** p
def ease_in(t, p=3): t = clamp(t); return t ** p
def ease_inout(t): t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def back_out(t, s=1.9):
    t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def elastic_out(t):
    t = clamp(t)
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - .75) * (2 * math.pi / 3)) + 1
def window(t, a, b, fi=.2, fo=.2):
    """1 inside [a,b] with fades"""
    if t < a - fi or t > b + fo: return 0.0
    return smooth((t - (a - fi)) / max(fi, 1e-6)) * (1 - smooth((t - b) / max(fo, 1e-6)))
def mixc(a, b, t): return tuple(lerp(x, y, t) for x, y in zip(a, b))


class Audio:
    def __init__(self):
        a = json.load(open(f'{WORK}/analysis.json'))
        g = json.load(open(f'{WORK}/grid.json'))
        self.fps = a['fps']
        self.arr = {k: np.array(a[k], np.float32) for k in ('rms', 'rms_vocal', 'rms_drum', 'rms_bass', 'low', 'mid', 'high', 'centroid')}
        self.beat = g['beat']; self.g0 = g['eighth_offset']; self.bar_len = 4 * self.beat
        h = json.load(open(f'{WORK}/hits.json'))
        self.hits = {k: np.array([x[0] for x in v]) for k, v in h.items()}
        self.hit_str = {k: np.array([x[1] for x in v]) for k, v in h.items()}
        self.dur = a['duration']

    def __call__(self, name, t, smooth_frames=0):
        a = self.arr[name]; i = t * self.fps
        j = int(clamp(i, 0, len(a) - 2))
        if smooth_frames:
            lo = max(0, j - smooth_frames); return float(a[lo:j + 1].mean())
        f = i - j
        return float(a[j] * (1 - f) + a[j + 1] * f)

    def bars(self, t): return (t - self.g0) / self.bar_len
    def beats(self, t): return (t - self.g0) / self.beat
    def bar_t(self, k): return self.g0 + k * self.bar_len
    def beat_t(self, k): return self.g0 + k * self.beat
    def beat_phase(self, t): return self.beats(t) % 1.0

    def pulse(self, t, kind='kick', decay=7.0, thresh=0.0):
        """envelope after the most recent hit of a kind"""
        hs = self.hits[kind]; j = np.searchsorted(hs, t) - 1
        if j < 0: return 0.0
        st = self.hit_str[kind][j]
        if st < thresh: return 0.0
        return float(min(1.2, st) * math.exp(-(t - hs[j]) * decay))

    def beat_pulse(self, t, decay=6.0):
        return math.exp(-((t - self.g0) % self.beat) * decay)

    def last_hit(self, t, kind='kick'):
        hs = self.hits[kind]; j = np.searchsorted(hs, t) - 1
        return (hs[j], j) if j >= 0 else (-1e9, -1)


# ---------------- stateless potato emitters ----------------
def potato_fountain(t, t0, t1, rate, origin, seed=0, speed=(3.2, 4.5), spread=1.2, g=-6.5, life=2.4,
                    radius=(.22, .38), face_p=.3, z=(-1.5, 1.0)):
    """potatoes launched from origin (world units) between t0 and t1, `rate` per second"""
    out = []
    if t < t0: return out
    n0 = max(0, int((t - life - t0) * rate)); n1 = int((min(t, t1) - t0) * rate) + 1
    for k in range(n0, n1):
        ts = t0 + k / rate
        tau = t - ts
        if tau < 0 or tau > life: continue
        r = np.random.RandomState(seed * 7919 + k)
        ang = r.uniform(-spread, spread) * .5 + math.pi / 2
        sp = r.uniform(*speed)
        vx, vy = math.cos(ang) * sp, math.sin(ang) * sp
        zz = r.uniform(*z)
        x = origin[0] + vx * tau; y = origin[1] + vy * tau + .5 * g * tau * tau
        rad = r.uniform(*radius) * min(1, tau * 6)
        axis = tuple(r.normal(size=3)); w = r.uniform(2, 7)
        out.append(((x, y, origin[2] + zz), rad, axis, w * tau + r.uniform(0, 6), r.uniform(0, 50), float(r.rand() < face_p)))
    return out


def potato_rain(t, t0, t1, rate, seed=0, x_range=(-3.6, 3.6), top=2.4, fall=(2.0, 3.5), radius=(.2, .4), face_p=.25):
    out = []
    if t < t0: return out
    life = 3.0
    n0 = max(0, int((t - life - t0) * rate)); n1 = int((min(t, t1) - t0) * rate) + 1
    for k in range(n0, n1):
        ts = t0 + k / rate; tau = t - ts
        if tau < 0 or tau > life: continue
        r = np.random.RandomState(seed * 104729 + k)
        x = r.uniform(*x_range); z = r.uniform(-2, .8)
        y = top + 0.4 - r.uniform(*fall) * tau - 1.2 * tau * tau
        out.append(((x, y, z), r.uniform(*radius), tuple(r.normal(size=3)), r.uniform(2, 6) * tau + r.uniform(0, 6), r.uniform(0, 50), float(r.rand() < face_p)))
    return out


def potato_uniforms(pots, glow=0.0, squash=0.0):
    pot, rot, info = [], [], []
    for (pos, rad, axis, ang, seed, face) in pots[:48]:
        pot += [*pos, rad]; rot += [*axis, ang]; info += [seed, face, squash, glow]
    return dict(uCount=min(len(pots), 48), uPot=pot or [0] * 4, uRot=rot or [0, 1, 0, 0], uInfo=info or [0] * 4)


# ---------------- stateless 2D particles ----------------
SHAPES = dict(circle=0, star=1, confetti=2, bat=3, heart=4, button=5, thumb=6, medal=7, ring=8)


def burst(t, t0, origin, n, seed=0, shape='star', colors=((1, .8, .2),), speed=(300, 900), size=(20, 50), g=900,
          life=1.6, spin=6.0, outline=1.0, glow=0.0, alpha=1.0, fade=False):
    """radial burst of particles at time t0 from origin (px)"""
    out = []
    tau = t - t0
    if tau < 0 or tau > life: return out
    for k in range(n):
        r = np.random.RandomState(seed * 31337 + k)
        a = r.uniform(0, 2 * math.pi); sp = r.uniform(*speed)
        x = origin[0] + math.cos(a) * sp * tau
        y = origin[1] + math.sin(a) * sp * tau + .5 * g * tau * tau
        s = r.uniform(*size) * (1 - (tau / life) ** 3)
        c = colors[k % len(colors)]
        sh = SHAPES[shape] if isinstance(shape, str) else SHAPES[shape[k % len(shape)]]
        out.append([x, y, s, s * (.55 if sh == 2 else 1), r.uniform(-1, 1) * spin * tau, sh, *c, alpha * ((1 - tau / life) if fade else 1.), outline, glow, 0, 0])
    return out


def drift(t, n, seed, shape, colors, area=(1920, 1080), size=(14, 40), vy=(-30, 60), sway=40, spin=1.0,
          alpha=1.0, outline=0.0, glow=0.0, period=None):
    """ambient floating particles wrapping around the screen"""
    out = []
    W, H = area
    for k in range(n):
        r = np.random.RandomState(seed * 7777 + k)
        x0, y0 = r.uniform(0, W), r.uniform(0, H)
        v = r.uniform(*vy)
        y = (y0 + v * t) % (H + 120) - 60
        x = x0 + math.sin(t * r.uniform(.5, 1.5) + k) * sway
        s = r.uniform(*size)
        sh = SHAPES[shape] if isinstance(shape, str) else SHAPES[shape[k % len(shape)]]
        c = colors[k % len(colors)]
        out.append([x, y, s, s * (.5 if sh == 2 else 1), t * spin * r.uniform(-1, 1) + k, sh, *c, alpha, outline, glow, 0, 0])
    return out

PART_LAYOUT = [('iPos', 2), ('iSize', 2), ('iRot', 1), ('iShape', 1), ('iColor', 4), ('iParam', 4)]


# ---------------- camera of potatoes.frag: ro=(0,0,6), rd=normalize(ndc,-1.6), ndc height 1 ----------------
def world_xy(px, py, z, W=1920, H=1080):
    """screen px (y down) -> world (x, y) on the plane at depth z"""
    s = (6 - z) / 1.6
    return ((px - W / 2) / H * s, (H / 2 - py) / H * s)

def screen_xy(x, y, z, W=1920, H=1080):
    s = (6 - z) / 1.6
    return (W / 2 + x / s * H, H / 2 - y / s * H)
