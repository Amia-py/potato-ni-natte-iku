"""Line-art shot list — pencil-grid cut.

Rules this cut obeys:

* Character-intro pages use the event's own card art, traced to contour.
* Anywhere else, only the person who is actually singing that line appears — the
  cast is read from lyrics_timing.json at draw time, so a page can change cast when
  the line changes.
* Every page carries drawn stage furniture (curtain, spot, floor, mic, speaker,
  bulbs, audience, confetti, notes, clock, crate, ladder, rope, steam, gear, film
  strip, ticket, rain, window, loose paper) so nothing is potato + person + type alone.
* Lyrics sit in the right margin in five rotating settings, never on the singer's side.
* Transitions are film terms, including the slice-slip and inverted flash of the reference.
"""
import math
import random
import numpy as np
from . import typo, props
from .common import *
from .typo import PAPER, INK, GRAY, YELLOW, PINK, GREEN, PURPLE, TEAL, CREAM, GOLD
from .lyrics import MEMBER

FILM = dict(uRetro=0., uSat=.92, uContrast=1.03, uGrain=.024, uVignette=.24, uCA=.35, uBloomAmt=.5,
            uBloomTint=(1., .80, .58), uLift=.55, uLiftCol=(.10, .075, .05), uBg=(.906, .875, .784),
            uHalftone=.0, uMono=0., uFlash=(1., 1., 1., 0.))

SING = {'神代類': 'rui', '天馬司': 'tsukasa', '草薙寧々': 'nene', '鳳えむ': 'emu', '初音ミク': 'miku'}
EN = {'rui': 'KAMISHIRO', 'tsukasa': 'TENMA', 'nene': 'KUSANAGI', 'emu': 'OTORI', 'miku': 'MIKU'}


def build_shots(m):
    from .mv import ORDER, NAMES
    au = m.au; W, H = m.W, m.H
    B = au.bar_t
    shots = []
    POSE = [0]

    # ---------------------------------------------------------------- page furniture
    def pg(t, mode=0., rules=1., frame=1., film=1., accent=None, glow=1., grid=0.):
        m.paper(uAccent=accent or YELLOW, uMode=mode, uRules=rules, uFrame=frame, uFilm=film,
                uGlow=glow, uGrid=grid)

    def plate(tex, cx, cy, maxw, maxh, alpha=1., rot=0., lit=None, uv=(0, 0, 1, 1), flip=False):
        ar = tex.width / tex.height
        maxh = min(maxh * 1.20, H * .98); maxw = min(maxw * 1.10, W * .50)
        w = min(maxw, maxh * ar); h = w / ar
        cx = min(cx, W * .40)
        if flip:
            uv = (uv[2], uv[1], uv[0], uv[3])
        tint = (*lit, 1.) if lit else (1., 1., 1., 0.)
        m.img(tex, cx, cy, w, h, rot, uv, uOpacity=alpha, uTint=tint, uPad=0.)

    def full(tex, zoom=1.05, pan=(0., 0.), alpha=1., lit=None, flip=False):
        tint = (*lit, 1.) if lit else (1., 1., 1., 0.)
        ar = tex.width / tex.height
        h = H * .92 * min(zoom, 1.25)
        w = h * ar
        if w > W * .50:
            w = W * .50; h = w / ar
        uv = (1, 0, 0, 1) if flip else (0, 0, 1, 1)
        m.img(tex, W * .25 + pan[0] * W * .08, H * .53 + pan[1] * H * .45, w, h, 0.,
              uv, uOpacity=alpha, uTint=tint, uPad=0.)

    def rule(x, y, w, h=2., ink=INK, alpha=1.):
        m.rect(x, y, w, h, ink, alpha)

    def disc(cx, cy, r, col, alpha=1.):
        if getattr(m, '_white', None) is None:
            m.rect(0, 0, 1, 1, (0, 0, 0), 0.)
        m.img(m._white, cx, cy, r * 2, r * 2, 0., uMask=2., uTint=(*col, 1.), uOpacity=alpha)

    def mark(t, s, x=88, y=44, ink=INK, alpha=.42):
        typo.micro(m, s, x, y, 12, m.f_mono, ink, tracking=.3, alpha=alpha)

    # ---------------------------------------------------------------- casting
    def cast(t):
        """whoever is singing right now; nobody else is allowed on the page"""
        act = m.lyr.active(t, pre=.26, post=.58)
        out = []
        for L in act[:2]:
            for s in L.get('singers', []):
                k = SING.get(s)
                if k and k not in out:
                    out.append(k)
        return out

    def next_pose(who):
        """walk this character's sheets so none goes unused, one step per shot"""
        n = len(m.pose_files(who))
        i = m._pi.get(who, 0)
        m._pi[who] = i + 1
        return i % max(1, n)

    def held_pose(who, slot, gi=0):
        """a pose must not change inside a shot; it is chosen the first frame and kept"""
        key = (getattr(m, '_shot_id', 0), who, slot, gi)
        cache = m._pose_cache
        if key not in cache:
            cache[key] = next_pose(who)
        return cache[key]

    def actor(t, slot=0, h=.60, x=None, alpha=1., lit=None, pose=None, flip=None, ghosts=2):
        """the singer, plus one or two of their other sheets ghosted behind"""
        c = cast(t)
        if not c:
            return None
        who = c[slot % len(c)]
        h = min(h, .52)
        cx = x if x is not None else (W * .20 + slot * W * .17)
        k = held_pose(who, slot) if pose is None else pose
        fl = ((k // 2) % 2 == 1) if flip is None else flip
        plate(m.gen_ln(who, k), cx, H * .60, W * .30, H * h, alpha=alpha, lit=lit, flip=fl)
        for g in range(ghosts):
            kg = held_pose(who, slot, g + 1)
            gx = cx + W * .105 * (g + 1)
            if gx > W * .44:
                gx = cx - W * .10 * (g + 1)
            plate(m.gen_ln(who, kg), gx, H * .62, W * .24, H * h * .74, alpha=alpha * .22,
                  lit=lit, flip=((kg // 2) % 2 == 1))
        return who

    # ---------------------------------------------------------------- lyrics
    def lyrics(t, lit=None, accent=None, **ignore):
        act = m.lyr.active(t, pre=.30, post=.62)
        if not act: return
        col = lit or INK
        acc = accent or YELLOW
        tpl = getattr(m, '_shot_id', 0) % 5      # set per shot: no mid-shot layout pop
        L = act[0]
        n = max(1, len(L['glyphs']))
        avail = H * .90
        y0 = H * .06
        avail = H * .87
        if tpl == 0:                                   # tall column near the edge
            s = min(52., avail / (n * 1.40))
            typo.lyric_v(m, L, t, W - 132, y0, s, m.f_serif, 1.40, col, acc)
            m.rect(W - 168, y0, 1.6, min(avail, n * s * 1.40), col, .22)
        elif tpl == 1:                                 # two stepped columns
            for j, LL in enumerate(act[:2]):
                nn = max(1, len(LL['glyphs']))
                ss = min(46., avail / (nn * 1.42))
                typo.lyric_v(m, LL, t, W - 126 - j * ss * 1.44, y0 + H * .02, ss, m.f_serif, 1.42, col, acc)
        elif tpl == 2:                                 # flat, right aligned, low
            txt = ''.join(g['ch'] for g in L['glyphs'])
            s = 48.
            if len(txt) * s > W * .46: s = W * .46 / max(1, len(txt))
            typo.htext(m, txt, W - 110, H * .62, s, m.f_decol, col, align='right', tracking=.02, alpha=.96)
            m.rect(W - 110 - len(txt) * s, H * .655, len(txt) * s, 2.4, acc, .6)
        elif tpl == 3:                                 # one glyph per beat, huge
            s = min(70., avail / (n * 1.30))
            typo.lyric_v(m, L, t, W - 148, y0, s, m.f_serif, 1.30, col, acc)
        else:                                          # two short rows, stacked right
            for j, LL in enumerate(act[:2]):
                txt = ''.join(g['ch'] for g in LL['glyphs'])
                s = 46.
                if len(txt) * s > W * .44: s = W * .44 / max(1, len(txt))
                typo.htext(m, txt, W - 88, H * (.28 + j * .10), s, m.f_decol, col,
                           align='right', tracking=.05, alpha=.95 - j * .16)

    # ---------------------------------------------------------------- shot wrapper
    def add(b0, b1, fn, trans=None, t0=None, t1=None, amt=.026, ly=None):
        POSE[0] += 1
        sid = POSE[0]

        def g(t, lt, d, _f=fn, _amt=amt, _ly=ly, _sid=sid):
            m._pose_k = _sid
            m._shot_id = _sid
            r = dict(_f(t, lt, d) or {})
            if _ly is not False:
                lyrics(t, **(_ly or {}))
            r.setdefault('uBallScale', 1.0 + _amt * clamp(lt / max(d, .01)))
            return r

        shots.append(dict(t0=B(b0) if t0 is None else t0, t1=B(b1) if t1 is None else t1, fn=g, trans=trans))

    def kick(t, d=7.): return au.pulse(t, 'kick', d)

    # ================================================================ 01 leader
    def s_leader(t, lt, d):
        pg(t, rules=0., frame=0., grid=.55)
        props.filmstrip(m, 60, H * .10, W * .40, H * .13, n=5, a=.32)
        props.filmstrip(m, W * .56, H * .77, W * .38, H * .12, n=5, a=.26)
        props.clock(m, W * .78, H * .22, 66, t, a=.30)
        n = 3 - int(clamp(lt / (d / 3.), 0, 2.999))
        cx, cy, r = W * .5, H * .48, 190
        disc(cx, cy, r, INK, .88)
        disc(cx, cy, r - 6, PAPER, 1.)
        props.radar(m, cx, cy, r - 6, ((lt / (d / 3.)) % 1.) * 2 * math.pi, a=.42, tails=30, span=.55)
        rule(cx - r + 8, cy - 1.5, (r - 8) * 2, 3, INK, .5)
        rule(cx - 1.5, cy - r + 8, 3, (r - 8) * 2, INK, .5)
        typo.display(m, str(n), cx, cy, 176, m.f_round, INK, pulse=False)
        mark(t, 'WONDERLANDS×SHOWTIME   ·   REEL 01   ·   24 FPS', 88, H * .90, INK, .48)
        return dict(FILM, uLift=.35)

    add(0, 3, s_leader)

    # ================================================================ 02 title
    def s_title(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., accent=GOLD, grid=.30)
        props.curtain(m, W, H, close=.62, c=(.10, .09, .07), a=.55, folds=8)
        props.spot(m, W, H, W * .5, 0., rx=.34, alpha=.10, c=CREAM)
        props.bulbs(m, W, W * .16, W * .84, H * .11, n=15, a=.55, beat=kick(t))
        props.confetti(m, W, H, t, n=26, a=.30, c=CREAM, seed=7)
        rule(W * .40, H * .30, W * .20, 2, CREAM, .42)
        typo.display(m, 'potato', W * .5, H * .44, 150 + 6 * kick(t), m.f_pop, CREAM)
        typo.display(m, 'になっていく', W * .5, H * .57, 54, m.f_decol, CREAM, alpha=.9)
        typo.micro(m, '作詞・作曲・編曲   Neru     歌   ワンダーランズ×ショウタイム / 初音ミク', W * .5, H * .76,
                   13, m.f_dot, CREAM, align='center', tracking=.1, alpha=.55)
        return dict(FILM, uLift=.42)

    add(3, 5, s_title, trans=(11, .30))

    # ================================================================ 03 members — this event's cards
    MEM_CARD = {'tsukasa': 'tsu_a', 'emu': 'emu_a', 'nene': 'nen_a', 'rui': 'rui_a', 'miku': 'miku'}
    DRESS = {'rui': 'ladder', 'tsukasa': 'crate', 'emu': 'confetti', 'nene': 'window', 'miku': 'gear'}

    def member_shot(who, side, idx):
        def fn(t, lt, d):
            pg(t, rules=0., frame=1., grid=.35)
            ap = ease_out(clamp(lt / .30))
            tex = m.intro_ln(who)
            ar = tex.width / tex.height
            bh = H * .88 * min(1., .9 + lt * .2)
            bw = bh * ar
            if bw > W * .46:
                bw = W * .46; bh = bw / ar
            bx = W * .50 - bw * .5 + (W * .055 if side > 0 else -W * .055)
            by = H * .06
            m.img(tex, bx + bw * .5, by + bh * .5, bw, bh, 0., (0, 0, 1, 1),
                  uOpacity=ap, uTint=(1., 1., 1., 0.), uPad=0.)
            # a hairline plate mark, offset so it reads as a printed frame
            for (x0, y0, w0, h0) in ((bx - 14, by - 14, bw + 28, 1.6), (bx - 14, by + bh + 12, bw + 28, 1.6),
                                     (bx - 14, by - 14, 1.6, bh + 28), (bx + bw + 12, by - 14, 1.6, bh + 28)):
                m.rect(x0, y0, w0, h0, INK, .34 * ap)
            props.filmstrip(m, W * .03, H * .10, W * .16, H * .40, n=3, a=.20 * ap)
            props.notes(m, W, H, t, n=6, a=.20, x0=.02, x1=.20)
            props.confetti(m, W, H, t, n=16, a=.16, seed=idx)
            jp, en = NAMES[who]
            ty = min(by + bh + 46, H * .92)
            m.rect(88, ty - 34, 40 + 46 * len(jp), 68, INK, .92 * ap)
            m.rect(88, ty - 34, 5, 68, YELLOW, .95 * ap)
            typo.display(m, jp, 104, ty, 40, m.f_decol, CREAM, align='left', alpha=ap, tracking=.03)
            typo.micro(m, f'{en}   ·   CUT {idx:02d}', 108, ty + 44, 12, m.f_mono, INK,
                       tracking=.2, alpha=ap * .55)
            return dict(FILM, uLift=.5)
        return fn

    for i, who in enumerate(ORDER):
        add(5 + .82 * i, 5.82 + .82 * i, member_shot(who, 1 if i % 2 == 0 else -1, i + 1),
            trans=(10, .24), amt=.012)

    # ================================================================ 04 stage plate
    def s_stage(t, lt, d):
        pg(t, rules=0., frame=1., grid=.5)
        props.curtain(m, W, H, close=.34, c=INK, a=.6, folds=7)
        props.spot(m, W, H, W * .46, H * .02, rx=.30, alpha=.18)
        props.floor(m, W, H, y=.74, a=.5)
        props.mic(m, W * .44, H * .80, h=250, a=.95)
        props.mic(m, W * .56, H * .80, h=210, a=.60, tilt=.12)
        props.bulbs(m, W, W * .10, W * .90, H * .10, n=13, a=.7, beat=kick(t))
        props.crate(m, W * .06, H * .60, 120, 104, a=.40)
        props.crate(m, W * .06 + 30, H * .44, 84, 70, a=.32)
        props.notes(m, W, H, t, n=8, a=.28)
        m.potato(W * .24, H * .60, 96 + 4 * kick(t), seed=.31, face=0, squash=.03,
                 fill=(.94, .86, .66), accent=YELLOW)
        mark(t, 'FIG. 01  ·  THE POTATO  ·  ON STAGE', 88, H * .90, INK, .45)
        return dict(FILM)

    add(9.1, 10.6, s_stage, trans=(12, .26))

    def s_house(t, lt, d):
        """the house before the curtain: this page exists so no gap is left in the cut"""
        pg(t, rules=0., frame=1., grid=.45)
        props.curtain(m, W, H, close=.20, c=INK, a=.62, folds=8)
        props.spot(m, W, H, W * .50, 0., rx=.30, alpha=.14)
        props.audience(m, W, H, y=.80, n=15, a=.26)
        props.bulbs(m, W, W * .12, W * .88, H * .17, n=12, a=.55, beat=kick(t))
        props.floor(m, W, H, y=.80, a=.42)
        props.rope(m, W * .84, 0, H * .30, t, a=.30, sway=.26)
        props.filmstrip(m, 60, H * .06, W * .34, H * .10, n=4, a=.34)
        props.notes(m, W, H, t, n=7, a=.30)
        typo.display(m, '開演', W * .50, H * .36, 62, m.f_decol, INK, tracking=.30,
                     alpha=.72 * ease_out(clamp(lt / .5)))
        return dict(FILM, uLift=.5)

    add(10.6, 12, s_house, trans=(10, .24))

    # ================================================================ 05 verse 1a
    def s_v1a(t, lt, d):
        pg(t, rules=0., frame=1., grid=.42)
        props.spot(m, W, H, W * .24, 0., rx=.24, alpha=.20)
        props.floor(m, W, H, y=.79, a=.44)
        props.rain(m, W, H, t, n=44, a=.24)
        actor(t, 0, h=.92)
        mark(t, 'TAKE 01', 88, H * .90, INK, .4)
        return dict(FILM, uLift=.5)

    add(12, 14, s_v1a, trans=(13, .20))

    # ================================================================ 06 verse 1b
    def s_v1b(t, lt, d):
        pg(t, rules=0., frame=1., grid=.5)
        props.papers(m, W, H, t, n=14, a=.34, x=.02, y=.94)
        actor(t, 0, h=.90, x=W * .23)
        props.floor(m, W, H, y=.86, a=.36)
        return dict(FILM, uLift=.5)

    add(14, 16, s_v1b, trans=(10, .22))

    # ================================================================ 07 verse 1c (ink page)
    def s_v1c(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., accent=YELLOW, grid=.22)
        props.steam(m, W, H, t, n=16, a=.28, c=CREAM, x0=.02, x1=.62)
        props.bulbs(m, W, W * .06, W * .62, H * .12, n=8, a=.55, c=GOLD, beat=kick(t))
        actor(t, 0, h=.96, alpha=.62, lit=CREAM, x=W * .22)
        m.rect(0, 0, W, H, (.05, .04, .03), .28)
        typo.display(m, '幕間', W * .54, H * .30, 58, m.f_pop, CREAM, align='left')
        typo.micro(m, 'INTERLUDE  ·  THE HOUSE LIGHTS ARE DOWN', W * .54, H * .38, 12, m.f_mono, CREAM,
                   tracking=.26, alpha=.55)
        return dict(FILM, uLift=.30, uVignette=.34)

    add(16, 21, s_v1c, trans=(11, .28), ly=dict(lit=CREAM))

    # ================================================================ 08 blackout
    def s_blackout(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., glow=.6, grid=.25)
        props.curtain(m, W, H, close=.30, c=(.10, .09, .07), a=.55, folds=7)
        props.spot(m, W, H, W * .52, 0., rx=.22, alpha=.10, c=CREAM)
        props.steam(m, W, H, t, n=18, a=.26, c=CREAM, x0=.10, x1=.92)
        props.rope(m, W * .70, 0, H * .58, t, a=.30, c=CREAM, sway=.30)
        props.bulbs(m, W, W * .18, W * .82, H * .16, n=8, a=.42, c=GOLD, beat=kick(t))
        a = 1 - clamp(lt / max(d, .1)) * .35
        typo.display(m, '転換', W * .50, H * .47, 74, m.f_decol, CREAM, tracking=.22, alpha=.55 * a)
        rule(W * .34, H * .56, W * .32 * ease_out(clamp(lt / .4)), 1.5, CREAM, .30 * a)
        return dict(FILM, uLift=.22, uBg=(.04, .032, .026))

    add(21, 22, s_blackout, trans=(8, .12))

    # ================================================================ 09 pre-chorus
    def s_pre1(t, lt, d):
        pg(t, rules=0., frame=1., grid=.4)
        props.crate(m, W * .02, H * .58, 150, 120, a=.55)
        props.crate(m, W * .02 + 40, H * .40, 92, 76, a=.45)
        props.confetti(m, W, H, t, n=34, a=.45, seed=11)
        actor(t, 0, h=.90, x=W * .26)
        props.floor(m, W, H, y=.88, a=.4)
        return dict(FILM, uLift=.5)

    add(22, 26, s_pre1, trans=(12, .24))

    # ================================================================ 10 one word
    def s_word(t, lt, d):
        pg(t, rules=0., frame=1., grid=.6)
        props.gear(m, W * .20, H * .30, 120, t * .8, a=.40)
        props.gear(m, W * .34, H * .20, 70, -t * 1.2, a=.28)
        actor(t, 0, h=.90, alpha=.95, x=W * .22)
        typo.display(m, '抗弁', W * .62, H * .48, 132 + 8 * kick(t), m.f_pop, INK, jitter=.04, seed=9)
        mark(t, 'NO DEFENCE', 88, H * .90)
        return dict(FILM, uLift=.46)

    add(26, 27, s_word, trans=(8, .08))

    # ================================================================ 11 chorus A
    def s_chorus1(t, lt, d):
        pg(t, rules=0., frame=1., grid=.3)
        props.audience(m, W, H, y=.93, n=14, a=.20)
        props.bulbs(m, W, W * .04, W * .60, H * .13, n=9, a=.6, beat=kick(t))
        props.spot(m, W, H, W * .24, H * .01, rx=.26, alpha=.16)
        actor(t, 0, h=.98)
        ap = ease_out(clamp((lt - .1) / .4))
        typo.display(m, '全部がpotatoに', W * .60, H * .52, 58, m.f_pop, INK, align='left', alpha=ap,
                     tracking=-.02, seed=3)
        rule(W * .60, H * .60, W * .32, 3, YELLOW, .8 * ap)
        return dict(FILM, uLift=.5)

    add(27, 31, s_chorus1, trans=(10, .20))

    # ================================================================ 12 chorus B (ink)
    def s_chorus2(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., accent=YELLOW, grid=.22)
        props.spot(m, W, H, W * .22, 0., rx=.20, alpha=.13, c=CREAM)
        props.steam(m, W, H, t, n=18, a=.24, c=CREAM, x0=.0, x1=.58)
        actor(t, 0, h=1.0, alpha=.64, lit=CREAM, x=W * .22)
        m.rect(0, 0, W, H, (.05, .04, .03), .34)
        k = kick(t)
        typo.display(m, 'potato', W * .52, H * .52, 104 + 8 * k, m.f_pop, CREAM, align='left', jitter=.02)
        typo.display(m, 'になっていく', W * .52, H * .63, 44, m.f_decol, CREAM, align='left', alpha=.85)
        return dict(FILM, uLift=.30, uVignette=.34)

    add(31, 35, s_chorus2, trans=(11, .26), ly=dict(lit=CREAM))

    # ================================================================ 13 chorus C
    def s_chorus3(t, lt, d):
        pg(t, rules=1., frame=1., grid=.34)
        props.floor(m, W, H, y=.66, a=.5)
        props.audience(m, W, H, y=.94, n=11, a=.16)
        props.notes(m, W, H, t, n=11, a=.42, x0=.02, x1=.60)
        ph = math.sin(t * 1.4)
        props.spot(m, W, H, W * .30, 0., rx=.24, alpha=.18)
        actor(t, 0, h=.80, x=W * .20, alpha=.92)
        m.potato(W * .30, H * .58 - ph * 10, 170 + 8 * kick(t), seed=.42, face=0,
                 squash=.03 + .03 * ph, rot=.05 * ph, fill=(.94, .86, .66), accent=YELLOW)
        for i in range(3):
            b = math.sin(t * 3.0 + i * 1.1)
            m.potato(W * (.12 + .06 * i), H * .80 - b * 9, 30 + 5 * b, seed=.2 + i * .19,
                     face=i % 3, squash=.06 + .03 * b, fill=(.93, .84, .64), accent=YELLOW)
        return dict(FILM)

    add(35, 40, s_chorus3, trans=(12, .22))

    # ================================================================ 14 KUSHA (ink)
    def s_kusha(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., accent=GOLD, grid=.18)
        props.rain(m, W, H, t, n=70, a=.30, c=CREAM)
        props.gear(m, W * .14, H * .22, 96, -t * .6, a=.30, c=CREAM)
        props.bulbs(m, W, W * .04, W * .62, H * .12, n=7, a=.45, c=GOLD, beat=kick(t))
        props.steam(m, W, H, t, n=16, a=.22, c=CREAM, x0=.0, x1=.56)
        props.crate(m, W * .03, H * .70, 104, 88, a=.26, c=CREAM)
        props.floor(m, W, H, y=.82, a=.26, c=CREAM)
        actor(t, 0, h=1.0, alpha=.58, lit=CREAM, x=W * .22)
        k = kick(t)
        typo.display(m, 'KUSHA', W * .60, H * .42, 118 + 12 * k, m.f_round, CREAM, rot=-.05, jitter=.03, seed=4)
        typo.display(m, 'KUSHA', W * .60, H * .59, 118 + 12 * k, m.f_round, GOLD, rot=.04, jitter=.03, seed=5)
        return dict(FILM, uCA=1.2, uLift=.26, uVignette=.36)

    add(40, 42, s_kusha, trans=(8, .10))

    # ================================================================ 15 parade
    def s_parade(t, lt, d):
        pg(t, rules=1., frame=1., grid=.36)
        props.bulbs(m, W, 0, W, H * .10, n=18, a=.6, beat=kick(t))
        props.confetti(m, W, H, t, n=46, a=.55, seed=5)
        props.floor(m, W, H, y=.70, a=.4)
        actor(t, 0, h=.78, x=W * .19, alpha=.95)
        for i in range(9):
            x = (W * .05 + i * 92 + (lt * 46)) % (W * 1.14) - 46
            bob = abs(math.sin(au.beats(t) * math.pi + i * .7)) * 18
            m.potato(x, H * .60 - bob, 30 + (i % 3) * 8, seed=.1 + i * .17, face=i % 3, squash=.05,
                     rot=.10 * math.sin(t * 1.3 + i), fill=(.93, .84, .64), accent=YELLOW)
        props.crate(m, W * .02, H * .58, 120, 104, a=.45)
        props.crate(m, W * .02 + 34, H * .42, 78, 66, a=.36)
        props.ladder(m, W * .40, H * .10, H * .78, w=40, rungs=7, a=.22)
        props.gear(m, W * .30, H * .24, 62, t * .5, a=.26)
        rule(0, H * .68, W, 2, INK, .30)
        typo.display(m, 'どろどろ', W * .30, H * .80, 50, m.f_decol, INK, alpha=.72, tracking=.08)
        return dict(FILM)

    add(42, 47, s_parade, trans=(10, .20))

    # ================================================================ 16 count
    def s_count(t, lt, d):
        pg(t, rules=0., frame=1., grid=.7)
        props.floor(m, W, H, y=.70, a=.34, rows=4)
        typo.display(m, '22', W * .5, H * .40, 180, m.f_pop, INK, jitter=.02, alpha=ease_out(clamp(lt / .2)))
        for i in range(22):
            x = W * .20 + i * (W * .60 / 21)
            rule(x, H * .58 - (18 if i % 4 == 0 else 0), 2, 18 if i % 4 == 0 else 8, INK, .42)
        return dict(FILM)

    add(47, 48, s_count, trans=(8, .08))

    # ================================================================ 17 verse 2a
    def s_v2a(t, lt, d):
        pg(t, rules=0., frame=1., grid=.44)
        props.window(m, W * .33, H * .07, W * .13, H * .17, a=.17, cols=2, rows=2)
        props.ladder(m, W * .40, H * .06, H * .92, w=44, rungs=9, a=.26)
        actor(t, 0, h=.92, x=W * .24)
        return dict(FILM, uLift=.5)

    add(48, 52, s_v2a, trans=(13, .18))

    # ================================================================ 18 verse 2b
    def s_v2b(t, lt, d):
        pg(t, rules=0., frame=1., grid=.4)
        props.crate(m, W * .02, H * .56, 130, 108, a=.5)
        props.papers(m, W, H, t, n=15, a=.32, x=.02, y=.96)
        actor(t, 0, h=.90, x=W * .26)
        typo.display(m, '勲章', W * .58, H * .30, 84, m.f_pop, INK, align='left', jitter=.03,
                     alpha=ease_out(clamp((lt - .2) / .4)))
        return dict(FILM, uLift=.5)

    add(52, 56, s_v2b, trans=(10, .22))

    # ================================================================ 19 build (ink)
    def s_build(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., grid=.24)
        props.rope(m, W * .44, 0, H * .70, t, a=.30, c=CREAM, sway=.24)
        props.steam(m, W, H, t, n=20, a=.26, c=CREAM, x0=.0, x1=.56)
        actor(t, 0, h=1.0, alpha=.56, lit=CREAM, x=W * .20)
        m.rect(0, 0, W, H, (.05, .04, .03), .34)
        props.bulbs(m, W, W * .50, W * .96, H * .14, n=7, a=.50, c=GOLD, beat=kick(t))
        props.crate(m, W * .04, H * .62, 118, 100, a=.34, c=CREAM)
        props.ladder(m, W * .36, H * .10, H * .86, w=38, rungs=8, a=.24, c=CREAM)
        for j in range(3):
            a = clamp((lt - j * .32) / .3)
            typo.display(m, '空回って', W * (.54 + j * .06), H * (.30 + j * .13), 46 + j * 16, m.f_decol,
                         CREAM, alpha=a * (.62 + .16 * j), tracking=.04, align='left')
        return dict(FILM, uCA=.8 + 1.1 * clamp(lt / d), uLift=.26, uVignette=.36)

    add(56, 60, s_build, trans=(11, .24), ly=dict(lit=CREAM))

    # ================================================================ 20 memory
    def s_memory(t, lt, d):
        pg(t, rules=0., frame=0., grid=.3)
        ap = ease_out(clamp(lt / .8))
        props.window(m, W * .02, H * .10, W * .30, H * .40, a=.26 * ap, cols=2, rows=3)
        props.rain(m, W, H, t, n=48, a=.22)
        actor(t, 0, h=.94, x=W * .23, alpha=ap)
        m.rect(0, 0, W, H, (.906, .875, .784), .10)
        mark(t, 'PLATE 04  ·  MEMORY', 88, H * .90, INK, .42)
        return dict(FILM, uLift=.42, uBloomAmt=.6, uVignette=.30)

    add(60, 64, s_memory, trans=(13, .30))

    # ================================================================ 21 spark
    def s_spark(t, lt, d):
        pg(t, rules=0., frame=0., grid=.8)
        props.confetti(m, W, H, t, n=60, a=.7, seed=2)
        typo.display(m, 'potato', W * .5, H * .5, 158, m.f_pop, INK, alpha=1 - clamp(lt / d))
        return dict(FILM, uFlash=(1., .96, .86, 1 - clamp(lt / .32)), uBloomAmt=.9)

    add(64, 65, s_spark, trans=(8, .06))

    # ================================================================ 22 final A
    def s_final1(t, lt, d):
        pg(t, rules=0., frame=1., grid=.32)
        props.audience(m, W, H, y=.88, n=15, a=.30)
        props.bulbs(m, W, W * .02, W * .58, H * .12, n=8, a=.55, beat=kick(t))
        props.confetti(m, W, H, t, n=30, a=.40, seed=9)
        actor(t, 0, h=1.0)
        m.rect(0, H * .72, W, H * .28, (.906, .875, .784), .80)
        k = kick(t)
        typo.display(m, '全部が', 88, H * .74, 40, m.f_decol, INK, align='left')
        typo.display(m, 'potato', 88, H * .80, 96 + 8 * k, m.f_pop, INK, align='left', jitter=.02, seed=6)
        return dict(FILM, uLift=.5)

    add(65, 70, s_final1, trans=(10, .18))

    # ================================================================ 23 final B (ink)
    def s_final2(t, lt, d):
        pg(t, mode=1., rules=0., frame=0., accent=GOLD, grid=.2)
        props.spot(m, W, H, W * .24, 0., rx=.22, alpha=.12, c=CREAM)
        props.steam(m, W, H, t, n=22, a=.22, c=CREAM, x0=.0, x1=.60)
        actor(t, 0, h=1.0, alpha=.55, lit=CREAM, x=W * .22)
        m.rect(0, 0, W, H, (.05, .04, .03), .38)
        gr = 1. + .10 * clamp(lt / max(d, .1))
        typo.display(m, '煮え切って', W * .56, H * .42, 62 * gr, m.f_pop, CREAM, tracking=.02)
        rule(W * .56, H * .52, W * .34, 2, GOLD, .62)
        a2 = ease_out(clamp((lt - 4.2) / .7))
        if a2 > .01:
            typo.display(m, 'ただバターに', W * .56, H * .60, 38, m.f_decol, GOLD, alpha=a2 * .78, tracking=.06)
        return dict(FILM, uLift=.28, uVignette=.34)

    add(70, 75, s_final2, trans=(11, .26), ly=dict(lit=CREAM))

    # ================================================================ 24 final C
    def s_final3(t, lt, d):
        pg(t, rules=1., frame=1., grid=.3)
        props.floor(m, W, H, y=.74, a=.46)
        props.notes(m, W, H, t, n=13, a=.5, x0=.02, x1=.62)
        props.bulbs(m, W, W * .04, W * .58, H * .12, n=7, a=.5, beat=kick(t))
        actor(t, 0, h=.98, x=W * .24)
        typo.display(m, 'KUSHA', W * .54, H * .68, 66, m.f_round, INK, rot=-.04, jitter=.03, seed=8, align='left')
        typo.display(m, 'KUSHA', W * .54, H * .77, 66, m.f_round, YELLOW, rot=.03, jitter=.03, seed=9, align='left')
        return dict(FILM, uLift=.48)

    add(75, 79, s_final3, trans=(12, .20))

    # ================================================================ 25 終演
    def s_outro(t, lt, d):
        pg(t, rules=0., frame=1., grid=.28)
        props.audience(m, W, H, y=.88, n=12, a=.24)
        props.bulbs(m, W, W * .10, W * .90, H * .14, n=14, a=.6, beat=kick(t))
        props.confetti(m, W, H, t, n=34, a=.34, seed=13)
        ap = ease_out(clamp(lt / .9))
        typo.display(m, '終演', W * .5, H * .42, 112, m.f_decol, INK, tracking=.18, alpha=ap)
        rule(W * .40, H * .54, W * .20 * ease_out(clamp((lt - .3) / .5)), 2, YELLOW, .75 * ap)
        for i in range(7):
            m.potato(W * (.62 + .05 * i), H * .84 - abs(math.sin(au.beats(t) * math.pi + i * .8)) * 9,
                     26, seed=.2 + i * .1, face=i % 3, squash=.03, fill=(.93, .84, .64), accent=YELLOW)
        return dict(FILM, uLift=.5)

    add(79, 82, s_outro, trans=(13, .26))

    # ================================================================ 26 programme + colophon (one page)
    def s_programme(t, lt, d):
        pg(t, rules=0., frame=1., grid=.30)
        ap = ease_out(clamp(lt / .6))
        props.filmstrip(m, 60, H * .08, W * .40, H * .10, n=5, a=.30 * ap)
        props.bulbs(m, W, W * .04, W * .46, H * .15, n=8, a=.44, beat=kick(t))
        props.ticket(m, W * .755, H * .55, W * .16, H * .13, a=.46 * ap)
        props.floor(m, W, H, y=.93, a=.24)
        typo.display(m, '演奏者', 88, H * .20, 78, m.f_decol, INK, align='left', alpha=ap)
        typo.micro(m, 'PROGRAMME  ·  ONE NIGHT ONLY', 92, H * .22 + 50, 12, m.f_mono, INK,
                   tracking=.24, alpha=ap * .5)
        rows = [('作詞・作曲・編曲', 'Neru', 22),
                ('歌', 'ワンダーランズ×ショウタイム  /  初音ミク', 22),
                ('出演', '天馬司  ·  鳳えむ  ·  草薙寧々  ·  神代類', 22)]
        y0 = H * .42
        for i, (lab, val, sz) in enumerate(rows):
            y = y0 + i * 74
            rule(88, y - 30, W * .50, 1.5, INK, .22 * ap)
            typo.micro(m, lab, 88, y, 15, m.f_dot, INK, tracking=.08, alpha=ap * .74)
            vf = m.f_dot if any(ord(ch) > 0x2e80 for ch in val) else m.f_mono
            typo.micro(m, val, 356, y - 4, sz, vf, INK, tracking=.05, alpha=ap * .58)
        # the credit line the user asked for, set large
        y = y0 + 3 * 88
        rule(88, y - 34, W * .56, 2, INK, .30 * ap)
        typo.micro(m, '制作', 88, y, 15, m.f_dot, INK, tracking=.08, alpha=ap * .74)
        typo.display(m, 'MV Opus5.5×DeepSeek V4.1 Flash', 88, y + 34, 54, m.f_decol, INK,
                     align='left', alpha=ap, tracking=.01)
        # colophon foot: what used to be the second page
        rule(88, H * .84, W * .82, 1.6, INK, .28 * ap)
        cols = [('編集', 'WONDERLANDS×SHOWTIME'), ('印刷', 'SEKAI PRINTING CO.'),
                ('発行', 'MV Opus5.5'), ('定価', '¥0')]
        for i, (k, v) in enumerate(cols):
            x = 88 + i * 330
            typo.micro(m, k, x, H * .87, 13, m.f_dot, INK, tracking=.16, alpha=ap * .6)
            typo.micro(m, v, x, H * .90, 12, m.f_mono, INK, tracking=.08, alpha=ap * .42)
        for i in range(5):
            m.potato(W * (.62 + .045 * i), H * .905, 22 - i * 2, seed=.3 + i * .17, face=i % 3,
                     squash=.02, fill=(.93, .84, .64), accent=YELLOW)
        return dict(FILM, uLift=.5)

    add(82, 89, s_programme, trans=(10, .26))

    # ================================================================ 28 curtain call
    def s_end(t, lt, d):
        pg(t, rules=0., frame=1., grid=.2)
        props.bulbs(m, W, W * .10, W * .90, H * .09, n=13, a=.5, beat=kick(t))
        typo.display(m, 'MV Opus5.5×DeepSeek V4.1 Flash', W * .5, H * .46, 46, m.f_decol, INK,
                     align='center', alpha=ease_out(clamp(lt / .5)))
        typo.micro(m, 'THANK YOU FOR COMING', W * .5, H * .57, 13, m.f_mono, INK, align='center',
                   tracking=.34, alpha=.42 * ease_out(clamp((lt - .4) / .6)))
        cl = ease_inout(clamp((lt - 1.0) / 1.7))
        props.curtain(m, W, H, close=cl, c=INK, a=.85, folds=11)
        return dict(FILM, uLift=.5)

    add(89, 91, s_end, t1=au.dur + 1, trans=(1, 1.2))
    return shots
