"""Stage furniture, drawn as ink on the page.

Everything here is a line element that is neither a potato, nor a person, nor type:
curtains, spotlights, footlights, floorboards, microphones, speaker stacks, marquee
bulbs, audience heads, confetti, notes, a clock, crates, ladders, ropes, steam,
gears, film strips, tickets, rain, a window. They exist to stop the page going empty
and to give the cut something to edit against.
"""
import math
import random

INK = (.098, .080, .062)
GRAY = (.40, .38, .36)
GOLD = (.80, .58, .18)


def _solid(m, x, y, w, h, c=INK, a=1., rot=0.):
    if a > .004 and w > .2 and h > .2:
        m.rect(x, y, w, h, c, a, rot)


def seg(m, x0, y0, x1, y1, th=2., c=INK, a=1.):
    """a line of any angle, drawn as one rotated slab"""
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    if ln < .5 or a <= .004:
        return
    _solid(m, (x0 + x1) * .5 - ln * .5, (y0 + y1) * .5 - th * .5, ln, th, c, a, math.atan2(dy, dx))


def radar(m, cx, cy, r, ang, a=.55, c=INK, tails=30, span=.62):
    """academy-leader sweep: a hand from the centre, afterglow as a fading wedge"""
    # afterglow: thin rays fanned behind the hand, fading with angle,
    # so the trail reads as one translucent pie slice without comb artefacts
    reach0 = span * .72
    n = max(34, int(reach0 * r / 2.0))
    for i in range(n):
        f = i / max(1, n - 1)
        aa = ang - f * reach0
        seg(m, cx + math.sin(aa) * r * .20, cy - math.cos(aa) * r * .20,
            cx + math.sin(aa) * r * .93, cy - math.cos(aa) * r * .93,
            2.2, c, a * (1. - f) ** 1.8 * .46)
    # the hand
    seg(m, cx, cy, cx + math.sin(ang) * r * .94, cy - math.cos(ang) * r * .94, 4.0, c, a * .8)
    # two fixed rings, so the dial reads as an instrument
    for rr in (.42, .70):
        for i in range(40):
            th = i * 2 * math.pi / 40
            _solid(m, cx + math.cos(th) * r * rr - 1.0, cy + math.sin(th) * r * rr - 1.0,
                   2.0, 2.0, c, a * .14)



# ---------------------------------------------------------------- 1 curtain
def curtain(m, W, H, close=1., c=INK, a=.9, folds=9, left=True, right=True):
    """two velvet legs drawn as folds of uneven width, with a valance across the top"""
    if close <= .003:
        return
    leg = W * .52 * close
    for side in ((0, 1) if (left and right) else ((0,) if left else (1,))):
        x0 = 0. if side == 0 else W - leg
        _solid(m, x0, 0, leg, H, (.906, .875, .784), .996)
        sw = leg / folds
        for i in range(folds + 1):
            # uneven fold spacing so it reads as cloth, not a grille
            t = i / folds
            xx = x0 + leg * (t + .018 * math.sin(i * 2.1))
            wgt = 1.4 + 2.6 * abs(math.sin(i * 1.7 + .4))
            _solid(m, xx, 0, wgt, H, c, a * (.22 + .30 * (i % 3 == 0)))
            _solid(m, xx + sw * .38, 0, 1.1, H, c, a * .16)
        edge = x0 + leg if side == 0 else x0
        _solid(m, edge - 2.4, 0, 4.8, H, c, a * .85)
    _solid(m, 0, 0, W, 12 * close, c, a * .30)


# ---------------------------------------------------------------- 2 spotlight
def _spot_tex(m):
    """a soft cone baked once: stacking translucent strips always bands"""
    if getattr(m, '_spottex', None) is None:
        import numpy as np
        N = 256
        yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
        u = (xx / (N - 1.)) * 2. - 1.
        v = yy / (N - 1.)
        half = .06 + .94 * v
        inside = np.clip((half - np.abs(u)) / .14, 0., 1.)
        a = inside * (1. - v * .50) * np.clip((1. - v) / .10, 0., 1.)
        rgba = np.zeros((N, N, 4), np.float32)
        rgba[..., :3] = 1.
        rgba[..., 3] = a
        m._spottex = m.ctx.texture((N, N), 4, (rgba[::-1] * 255).astype('uint8').tobytes())
    return m._spottex


def spot(m, W, H, cx, top_y=0., rx=.24, alpha=.16, c=INK, pool=False, steps=0):
    """a hard light cone from a lamp above, plus its pool on the floor"""
    if alpha <= .004:
        return
    m.img(_spot_tex(m), cx, top_y + H * .40, W * rx * 2.2, H * .80, 0.,
          uOpacity=alpha * .85, uTint=(*c, 1.))
    if pool:
        m.img(_white(m), cx, H * .955, W * rx * 2.3, W * rx * .20, 0., uMask=2., uTint=(*c, 1.),
              uOpacity=alpha * .9)


def _white(m):
    if getattr(m, '_white', None) is None:
        m.rect(0, 0, 1, 1, (0, 0, 0), 0.)
    return m._white


def ring(m, cx, cy, r, th=3., c=INK, a=.8, bg=None):
    """a ring drawn as beads: a filled-in inner disc would punch a white hole on dark pages"""
    n = max(28, int(r * .95))
    dot = max(2.2, (2 * math.pi * r / n) * .82)
    for i in range(n):
        ang = i * 2 * math.pi / n
        _solid(m, cx + math.cos(ang) * r - dot * .5, cy + math.sin(ang) * r - dot * .5,
               dot, dot, c, a)


# ---------------------------------------------------------------- 1 curtain
# ---------------------------------------------------------------- 2 spotlight
# ---------------------------------------------------------------- 3 floorboards
def floor(m, W, H, y=.86, rows=7, c=INK, a=.5):
    """perspective boards and a lip, so a figure stands on something"""
    yy = H * y
    _solid(m, 0, yy, W, 3, c, a)
    for i in range(rows):
        d = i / rows
        yy2 = yy + (H - yy) * (d ** 1.7)
        _solid(m, 0, yy2, W, 1.2, c, a * (.34 - .04 * i))
    for i in range(9):
        x0 = W * (i / 8.)
        seg(m, x0, yy, W * .5 + (x0 - W * .5) * 2.3, H, 1.2, c, a * .22)


# ---------------------------------------------------------------- 4 microphone
def mic(m, x, y, h=210, c=INK, a=.9, tilt=0.):
    """a microphone on a stand: capsule head, thin shaft, three legs"""
    top = y - h
    _solid(m, x - 2, top, 4, h, c, a)                     # shaft
    # capsule: a rounded box reads better than a circle at this size
    m.img(_white(m), x, top - 26, 44, 66, tilt, uMask=1., uMaskRound=21,
          uTint=(*c, 1.), uOpacity=a)
    for i in range(4):                                    # grille
        _solid(m, x - 15, top - 16 + i * 9, 30, 1.6, (.906, .875, .784), a * .9)
    _solid(m, x - 22, top - 60, 44, 8, c, a)              # yoke
    _solid(m, x - 2, top - 56, 4, 16, c, a)
    # tripod
    seg(m, x, y - 60, x - 46, y + 16, 3.4, c, a)
    seg(m, x, y - 60, x + 46, y + 16, 3.4, c, a)
    seg(m, x, y - 60, x, y + 20, 3.4, c, a)
    _solid(m, x - 52, y + 14, 104, 4, c, a * .8)


# ---------------------------------------------------------------- 5 speaker stack
def speaker(m, x, y, w=120, h=250, c=INK, a=.85):
    _solid(m, x, y, w, h, c, a * .12)
    _solid(m, x, y, w, 3, c, a)
    _solid(m, x, y + h - 3, w, 3, c, a)
    _solid(m, x, y, 3, h, c, a)
    _solid(m, x + w - 3, y, 3, h, c, a)
    for i, r in enumerate((.34, .26)):
        cy = y + h * (.34 + .42 * i)
        rr = w * r
        m.img(_white(m), x + w * .5, cy, rr * 2, rr * 2, 0., uMask=2., uTint=(*c, 1.), uOpacity=a * .16)
        ring(m, x + w * .5, cy, rr, 3.2, c, a * .55)
        _solid(m, x + w * .5 - rr, cy - 1, rr * 2, 1.6, c, a * .4)


# ---------------------------------------------------------------- 6 marquee bulbs
def bulbs(m, W, x0, x1, y, n=14, a=.8, c=GOLD, beat=0.):
    """a run of festoon lamps; they breathe on the beat"""
    if x1 <= x0:
        return
    for i in range(n):
        x = x0 + (x1 - x0) * i / max(1, n - 1)
        sag = math.sin(i / max(1, n - 1) * math.pi) * 22
        yy = y + sag
        if i:
            xp = x0 + (x1 - x0) * (i - 1) / max(1, n - 1)
            seg(m, xp, y + math.sin((i - 1) / max(1, n - 1) * math.pi) * 22, x, yy, 1.4, c, a * .4)
        lit = .55 + .45 * math.sin(i * 1.3 + beat * 6.28)
        _solid(m, x - 5, yy - 5, 10, 10, c, a * lit)
        m.img(_white(m), x, yy, 46, 46, 0., uMask=2., uTint=(*c, 1.), uOpacity=a * lit * .26)


# ---------------------------------------------------------------- 7 audience
def audience(m, W, H, y=.90, n=13, a=.34, c=INK):
    """heads and shoulders in silhouette, the cheapest way to fill a bottom band"""
    for i in range(n):
        x = W * (-.03 + 1.06 * i / (n - 1)) + (10 if i % 2 else -6)
        r = 15 + (i % 4) * 2.5
        yy = H * y + (8 if i % 3 else 0)
        m.img(_white(m), x, yy, r * 2, r * 2.1, 0., uMask=2., uTint=(*c, 1.), uOpacity=a)
        m.img(_white(m), x, yy + r * 1.35, r * 3.1, r * 1.7, 0., uMask=2., uTint=(*c, 1.),
              uOpacity=a * .92)


# ---------------------------------------------------------------- 8 confetti
def confetti(m, W, H, t, n=40, a=.6, c=INK, seed=1):
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.uniform(-.05, 1.05) * W
        sp = rnd.uniform(.06, .16)
        ph = rnd.uniform(0, 1)
        y = ((ph + t * sp) % 1.14 - .07) * H
        sw = math.sin(t * 2.1 + i)
        _solid(m, x0 + sw * 26, y, rnd.uniform(9, 16), rnd.uniform(5, 9), c, a * rnd.uniform(.3, .8),
               sw * .9)


# ---------------------------------------------------------------- 9 notes
def notes(m, W, H, t, n=9, a=.55, c=INK, x0=.06, x1=.94):
    for i in range(n):
        ph = (t * .07 + i * .137) % 1.
        x = W * (x0 + (x1 - x0) * ((i * .618) % 1.)) + math.sin(t + i) * 20
        y = H * (1.02 - ph * 1.05)
        s = 16 + (i % 3) * 6
        m.img(_white(m), x, y, s * 1.5, s, 0., uMask=2., uTint=(*c, 1.), uOpacity=a * (1 - ph * .5))
        _solid(m, x + s * .7, y - s * 1.5, 2., s * 1.5, c, a * (1 - ph * .5))
        _solid(m, x + s * .7, y - s * 1.5, s * .7, 2.4, c, a * (1 - ph * .5))


# ---------------------------------------------------------------- 10 clock
def clock(m, cx, cy, r, t, a=.8, c=INK, rate=.06):
    ring(m, cx, cy, r, 4., c, a)
    m.img(_white(m), cx, cy, r * 2.4, r * 2.4, 0., uMask=2., uTint=(*c, 1.), uOpacity=a * .10)
    for i in range(12):
        ang = i * math.pi / 6.
        seg(m, cx + math.sin(ang) * r * .82, cy - math.cos(ang) * r * .82,
            cx + math.sin(ang) * r * .94, cy - math.cos(ang) * r * .94, 2., c, a)
    ang = t * rate
    seg(m, cx, cy, cx + math.sin(ang) * r * .58, cy - math.cos(ang) * r * .58, 4., c, a)
    seg(m, cx, cy, cx + math.sin(ang * 12) * r * .80, cy - math.cos(ang * 12) * r * .80, 2.6, c, a)


# ---------------------------------------------------------------- 11 crate
def crate(m, x, y, w, h, a=.85, c=INK):
    _solid(m, x, y, w, h, c, a * .22)
    for (dx, dy, ww, hh) in ((0, 0, w, 3), (0, h - 3, w, 3), (0, 0, 3, h), (w - 3, 0, 3, h),
                             (0, h * .5 - 1.5, w, 3)):
        _solid(m, x + dx, y + dy, ww, hh, c, a)
    seg(m, x + 4, y + 4, x + w - 4, y + h - 4, 2.4, c, a * .7)
    seg(m, x + w - 4, y + 4, x + 4, y + h - 4, 2.4, c, a * .7)
    m.img(_white(m), x + w * .5, y + h * .5, w * 1.9, h * 1.9, 0., uMask=2., uTint=(*c, 1.),
          uOpacity=a * .04)


# ---------------------------------------------------------------- 12 ladder
def ladder(m, x, y0, y1, w=54, rungs=9, a=.8, c=INK):
    _solid(m, x, y0, 3.2, y1 - y0, c, a)
    _solid(m, x + w, y0, 3.2, y1 - y0, c, a)
    for i in range(rungs):
        y = y0 + (y1 - y0) * (i / max(1, rungs - 1))
        _solid(m, x, y, w, 2.6, c, a * .9)


# ---------------------------------------------------------------- 13 rope
def rope(m, x, y0, y1, t, a=.7, c=INK, sway=.01, hook=True):
    n = 18
    pts = []
    for i in range(n + 1):
        k = i / n
        pts.append((x + math.sin(t * 1.2 + k * 2.4) * 34 * k * sway * 40,
                    y0 + (y1 - y0) * k))
    for i in range(n):
        seg(m, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 2.2, c, a)
    if hook:
        hx, hy = pts[-1]
        ring(m, hx, hy + 12, 13, 3.4, c, a)
        _solid(m, hx - 2, hy - 8, 4, 22, c, a)


# ---------------------------------------------------------------- 14 steam
def steam(m, W, H, t, n=14, a=.30, c=INK, x0=.1, x1=.9):
    for i in range(n):
        ph = (t * .10 + i * .093) % 1.
        x = W * (x0 + (x1 - x0) * ((i * .371) % 1.)) + math.sin(t * 1.4 + i * 1.7) * 34
        y = H * (1.04 - ph * .8)
        r = (18 + 30 * ph) * (1 + .2 * math.sin(i))
        m.img(_white(m), x, y, r * 2, r * 1.6, 0., uMask=2., uTint=(*c, 1.),
              uOpacity=a * (1 - ph) * .8)


# ---------------------------------------------------------------- 15 gear
def gear(m, cx, cy, r, rot, teeth=12, a=.8, c=INK):
    ring(m, cx, cy, r, 5., c, a)
    for i in range(teeth):
        ang = rot + i * 2 * math.pi / teeth
        tx, ty = cx + math.sin(ang) * r * .96, cy - math.cos(ang) * r * .96
        _solid(m, tx - 7, ty - 7, 14, 14, c, a * .9, ang)


# ---------------------------------------------------------------- 16 film strip
def filmstrip(m, x, y, w, h, n=6, a=.75, c=INK, rot=0.):
    _solid(m, x, y, w, h, c, a * .10, rot)
    _solid(m, x, y, w, 2.6, c, a, rot)
    _solid(m, x, y + h - 2.6, w, 2.6, c, a, rot)
    for i in range(n):
        cx = x + w * (i + .5) / n
        _solid(m, cx, y - 5, 9, 5, c, a * .7, rot)
        _solid(m, cx, y + h, 9, 5, c, a * .7, rot)
        _solid(m, cx - w / n * .42, y + 5, 1.2, h - 10, c, a * .3, rot)


# ---------------------------------------------------------------- 17 ticket
def ticket(m, x, y, w, h, a=.85, c=INK, serif=True):
    _solid(m, x, y, w, h, c, a * .06)
    _solid(m, x, y, w, 2.4, c, a)
    _solid(m, x, y + h - 2.4, w, 2.4, c, a)
    _solid(m, x, y, 2.4, h, c, a)
    _solid(m, x + w - 2.4, y, 2.4, h, c, a)
    for i in range(int(h / 9)):
        _solid(m, x + w * .68, y + 6 + i * 9, 1.4, 5, c, a * .6)


# ---------------------------------------------------------------- 18 rain
def rain(m, W, H, t, n=60, a=.30, c=INK, seed=3):
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.uniform(0, 1.2) * W
        y0 = rnd.uniform(0, 1) * H
        sp = rnd.uniform(.5, 1.1) * H
        y = (y0 + t * sp) % (H * 1.1)
        ln = 26 + (i % 4) * 12
        seg(m, x0 - ln * .22, y, x0, y + ln, 1.6, c, a * rnd.uniform(.35, .9))


# ---------------------------------------------------------------- 19 window
def window(m, x, y, w, h, a=.8, c=INK, cols=2, rows=3):
    _solid(m, x, y, w, 4, c, a)
    _solid(m, x, y + h - 4, w, 4, c, a)
    _solid(m, x, y, 4, h, c, a)
    _solid(m, x + w - 4, y, 4, h, c, a)
    for i in range(1, cols):
        _solid(m, x + w * i / cols - 2, y, 4, h, c, a * .85)
    for i in range(1, rows):
        _solid(m, x, y + h * i / rows - 2, w, 4, c, a * .85)


# ---------------------------------------------------------------- 20 paper stack
def papers(m, W, H, t, n=8, a=.5, c=INK, x=.06, y=.78):
    """loose sheets drifting up, the cheapest motion for a static page"""
    for i in range(n):
        ph = (t * .09 + i * .13) % 1.
        px = W * x + math.sin(t * .8 + i * 2.2) * 60 + i * 30
        py = H * y - ph * H * .55
        _solid(m, px, py, 54, 72, c, a * (1 - ph) * .55, math.sin(t + i) * .4)
        _solid(m, px + 8, py + 10, 38, 1.4, c, a * (1 - ph) * .30, math.sin(t + i) * .4)
