"""Shot list. Bar k starts at au.bar_t(k) (116 BPM, 2.069 s per bar)."""
import math
import numpy as np
from .common import *
from .lyrics import MEMBER
from engine.text import layout

# member colours as tuples
CT, CE, CN, CR = MEMBER['tsukasa'], MEMBER['emu'], MEMBER['nene'], MEMBER['rui']
MCOL = {'tsukasa': CT, 'emu': CE, 'nene': CN, 'rui': CR, 'miku': MEMBER['miku'], 'miku_tail': MEMBER['miku']}
DARK = (.08, .03, .12, 1)
# fraction of the sprite height (from the top) where each character's skirt / coat hem ends
POT_HEM = {'rui': .66, 'tsukasa': .66, 'emu': .60, 'nene': .62, 'miku': .68, 'miku_tail': .68}


def in_pot(bowl, x_px, y_px, h_px, W=1920, H=1080):
    """Trim a standing sprite at the bowl's near rim.

    Returns (height, centre_y) of the shrunken quad: the sprite keeps its head at the same place and is cut
    where the near rim crosses it, so the pot's front wall hides everything below.
    """
    asp = W / H
    p_x = (x_px / W - bowl['cx']) * asp
    xr = p_x / bowl['rx']
    top = y_px - h_px / 2
    cut_px = (1. - (bowl['cy'] - bowl['ry'])) * H        # rim is a flat-ish line over the pot's width
    if abs(xr) < .98:
        y_arc = bowl['cy'] - bowl['ry'] * math.sqrt(1. - xr * xr)
        cut_px = (1. - y_arc) * H
    cut_px = min(max(cut_px, top + h_px * .08), top + h_px)
    return cut_px - top, (top + cut_px) / 2


def pot_surface(bowl, u, v, W=1920, H=1080):
    """world position for a point in the pot's soup surface: u across (-1..1), v back(0)..front(1)"""
    t = (1. - 2. * v) * .8                            # +: back half of the soup, -: front half
    sx = bowl['cx'] + u * math.sqrt(max(.15, 1. - t * t)) * .94 * bowl['rx'] * .8 / (W / H)
    sy = bowl['cy'] - .25 * bowl['ry'] + .8 * bowl['ry'] * t
    return world_xy(sx * W, (1. - sy) * H, .85 + .3 * v)      # front-row potatoes sit nearer, so they paint over the back row


def pot_floats(t, bowl, seed, n=9, n_front=0):
    """potatoes bobbing in the stew; they sit between the soup surface and the pot's near wall"""
    out = []
    for j in range(n + n_front):
        r = np.random.RandomState(seed * 977 + j)
        front = j >= n
        u = -.86 + 1.72 * ((j - n if front else j) + r.uniform(.2, .8)) / (n_front if front else n)
        v = r.uniform(.70, .92) if front else r.uniform(.12, .55)
        bob = math.sin(t * 3.1 + j * 1.3 + r.uniform(0, 6))
        x, y = pot_surface(bowl, u, v + .02 * bob)
        y += .05 + .04 * bob
        rad = r.uniform(.12, .17) * (1.15 if front else 1.)
        tilt = .35 + .25 * math.sin(t * (1.1 + .3 * r.rand()) + j)
        out.append(((x, y, .85 + .3 * (v + .02 * bob)), rad, (r.normal(), .2, r.normal()), tilt, r.uniform(0, 40),
                    float(r.rand() < .45)))
    return out


def build_shots(m):
    from .mv import ORDER, NAMES, BASE_MOTION, ROSTER
    au = m.au; W, H = m.W, m.H
    B = au.bar_t
    shots = []

    def add(b0, b1, fn, trans=None, t0=None, t1=None):
        shots.append(dict(t0=B(b0) if t0 is None else t0, t1=B(b1) if t1 is None else t1, fn=fn, trans=trans))

    def kick(t, d=7.): return au.pulse(t, 'kick', d)
    def snare(t, d=8.): return au.pulse(t, 'snare', d)

    def stand_in_pot(who, bowl, x, h=1000, dy=0., **kw):
        """Cast member standing in the soup: the sprite is cut just under the soup's back edge (the soup layer is drawn
        over it), so only the part above the waterline shows and the back wall never covers anyone."""
        q = min(abs(x - bowl['cx'] * W) / H / (.94 * bowl['rx']), .97)
        soup_cy = (1. - bowl['cy']) * H + .25 * bowl['ry'] * H
        edge = soup_cy - .8 * bowl['ry'] * H * math.sqrt(1. - q * q)       # soup back edge (screen y, down)
        top = edge + 14 + dy - POT_HEM[who] * h
        m.l2d(who, x, top + h / 2, h, uClip=((edge + 30 - top) / h, 1.), **kw)

    def line_color(L):
        return [CT, CE, CN, CR][L['idx'] % 4]

    def chorus_style(L):
        txt = L['text']
        st = dict(style='pop', glow=.6)
        if 'potato' in txt: st.update(style='potato', size=130)
        if 'KUSHA' in txt: st.update(style='shake', size=128)
        return st

    # ============================================================== 0. curtain (bars 0-3)
    def s_curtain(t, lt, d):
        open_ = ease_inout((t - B(2.85)) / .9)
        hat = au.pulse(t, 'hat', 10)
        bulbs = clamp(lt / B(2.8)) ** .5
        m.stage(uCurtain=open_ * .9, uBulbs=bulbs * (.5 + .5 * hat), uChase=au.beats(t) * (1 if t > B(2) else 0),
                uWall=(.20, .09, .03), uGrave=open_, uMoon=open_, uDeco=1., uCurtainCol=(.34, .05, .06),
                uSpot=[.5, .5 + .3 * math.sin(t * 1.3), .22, .6 + .4 * bulbs, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                uSpotCol=[1, .85, .6] + [0] * 9)
        a1 = window(t, B(.5), B(2.6), .6, .3)
        m.text('Wonderlands×Showtime', W / 2, H * .40, 70, font=m.at_serif, fill=(1, .85, .45), outline=.14, glow=.7, alpha=a1)
        m.text('presents', W / 2, H * .50, 40, font=m.at_serif, fill=(1, 1, 1), alpha=a1)
        a2 = window(t, B(1.6), B(2.8), .3, .2)
        m.text('HALLOWEEN SHOW', W / 2, H * .64, 54 * (1 + .05 * kick(t)), fill=(1, .55, .15), glow=1., alpha=a2, tracking=.08)
        return dict(uVignette=.9, uGrain=.06, uFlash=(1, .9, .7, .7 * math.exp(-max(0, t - B(3)) * 5) * (t > B(3))))

    add(0, 3, s_curtain)

    # ============================================================== 1. title (bars 3-5)
    def cauldron(t, cx=.5, cy=.33, rx=.42, ry=.11, glaze=(.12, .1, .14), stew=((.15, .5, .1), (.5, .95, .3)), layer=None):
        if layer in (None, 0):
            m.bg('bowl.frag', uLayer=0., uCenter=(cx, cy), uRadius=(rx, ry), uGlaze=glaze, uStewA=stew[0], uStewB=stew[1],
                 uBeat=kick(t)) if False else m.e.pass_('bowl.frag', m.cur, blend=True, uTime=t, uLayer=0., uCenter=(cx, cy),
                                                       uRadius=(rx, ry), uGlaze=glaze, uStewA=stew[0], uStewB=stew[1], uBeat=kick(t))
        if layer == 2:     # back wall, drawn behind the cast
            m.e.pass_('bowl.frag', m.cur, blend=True, uTime=t, uLayer=2., uCenter=(cx, cy), uRadius=(rx, ry), uGlaze=glaze,
                      uStewA=stew[0], uStewB=stew[1], uBeat=kick(t))
        if layer in (None, 1):
            m.e.pass_('bowl.frag', m.cur, blend=True, uTime=t, uLayer=1., uCenter=(cx, cy), uRadius=(rx, ry), uGlaze=glaze,
                      uStewA=stew[0], uStewB=stew[1], uBeat=kick(t))

    def s_title(t, lt, d):
        k = kick(t)
        m.stage(uCurtain=.9, uGrave=1., uMoon=1., uWall=(.19, .09, .035), uDeco=1., uCurtainCol=(.34, .05, .06),
                uSpot=[.25, .45, .2, .8, .75, .55, .2, .8, .5, .5, .3, .5 + .5 * k, 0, 0, 0, 0],
                uSpotCol=[1, .8, .45, .8, .85, .6, 1, .9, .55, 0, 0, 0])
        cauldron(t, layer=0)
        cauldron(t, layer=1)
        # potatoes fly out of the pot and must pass in front of its near wall
        pots = []
        for p_ in potato_fountain(t, B(3), B(5), 7, (0, -.75, -1.6), seed=1, speed=(3.9, 5.4), face_p=.5, z=(0., 2.4)):
            pos, rad, axis, ang, sd, face = p_
            if pos[2] < 1.2: rad *= .75          # keep them from poking through the pot walls
            pots.append((pos, rad, axis, ang, sd, face))
        m.potatoes(pots, rim=(.9, .5, 1.))
        # marquee plaque behind the wordmark, like the key art: cream border, gold rule, dark inset
        ap = (t - B(3) - .1) / .5
        sc = back_out(ap, 2.2) * (1 + .04 * k)
        y = H * .33
        if ap > 0:
            m.e.pass_('plaque.frag', m.cur, blend=True, uTime=t, uBeat=k, uReveal=clamp(sc, 0., 1.6),
                      uCenter=(.5, 1. - y / H), uSize=(W * .82 / H, H * .38 / H), uCrown=clamp(ap * 1.4, 0., 1.))
            _, w1 = layout(m.at, 'potato', 168 * sc); _, w2 = layout(m.at, 'になっていく', 104 * sc)
            x0 = W / 2 - (w1 + w2 + 16) / 2
            m.text('potato', x0, y + 16, 168 * sc, fill=(1., .96, .86), fill2=(1., .96, .86), line=(.11, .06, .03, 1),
                   outline=.15, glow=.8, align='left')
            m.text('になっていく', x0 + w1 + 16, y + 34, 104 * sc, fill=(1., .96, .86), line=(.11, .06, .03, 1),
                   outline=.16, glow=.4, align='left')
        a2 = clamp((t - B(3.5)) / .4)
        m.text('Wonderlands×Showtime × 初音ミク', W / 2, H * .60, 44, font=m.at_serif, fill=(1, .87, .58), alpha=a2)
        m.text('作詞・作曲・編曲 Neru', W / 2, H * .66, 34, font=m.at_serif, fill=(1., .95, .82), alpha=a2 * .9)
        m.text('MV Opus5.5', W / 2, H * .715, 30, font=m.at_serif, fill=(1., .97, .88), alpha=a2, outline=.2, glow=.35)
        m.parts(drift(t, 14, 3, 'bat', [(.1, .05, .15)], size=(40, 70), vy=(-40, -20), sway=80, spin=.3, alpha=.9))
        return dict(uCA=.6 + 1.5 * k, uShake=(0, .004 * k), uRetro=.72)

    add(3, 5, s_title, trans=(1, .5))

    # ============================================================== 2. members (bars 5-9)
    MEM_CARD = {'tsukasa': 'tsu_b', 'emu': 'emu_b', 'nene': 'nen_a', 'rui': 'rui_b', 'miku': 'miku'}
    MEM_MOT = {'tsukasa': 'm-proud11-smug', 'emu': 'w-special01-salute', 'nene': 'w-pure12-surprise', 'rui': 'm-cool02-tilthead',
           'miku': 'w-cool02-thumb'}

    def member_shot(who, side):
        def fn(t, lt, d):
            k = kick(t); c = MCOL[who]
            m.cover(m.card[MEM_CARD[who]], zoom=1.08 + .05 * lt, pan=(side * .6, 0), uDuo=.25, uDuoA=(.1, .03, .2), uDuoB=c, uHalftone=.25)
            m.comic(uColA=(0, 0, 0), uColB=c, uMode=0., uFocus=(.5 - side * .25, .5)) if False else None
            # diagonal colour band
            m.img(m.card[MEM_CARD[who]], W / 2 - side * 520, H / 2, 900, 1500, rot=side * .18, uTint=(*c, .85), uOpacity=.85)
            x = W / 2 - side * 520
            m.l2d(who, x, H * .62 + 30 * (1 - ease_out(lt / .4)), 1500, motion=MEM_MOT[who], mphase=lt * .8,
                  uOutline=7, uOutlineColor=(1, 1, 1), smile=.6)
            jp, en = NAMES[who]
            ap = ease_out((lt - .1) / .35)
            tx = W / 2 + side * 380 + (1 - ap) * side * 300
            m.text(jp, tx, H * .42, 150, font=m.at_serif, fill=(1, 1, 1), line=(*[x * .35 for x in c], 1), outline=.2, glow=.6, alpha=ap)
            m.text(en, tx, H * .56, 52, fill=c, outline=.14, alpha=ap, tracking=.15)
            m.parts(burst(t, B(5) + ORDER.index(who) * au.bar_len, (tx, H * .45), 26, seed=ORDER.index(who), shape='star',
                          colors=[c, (1, 1, 1)], speed=(300, 1100), size=(18, 46), life=1.4, glow=.5))
            return dict(uCA=.8 + 1.2 * k, uBloomAmt=.8)
        return fn

    for i, who in enumerate(ORDER):
        add(5 + .82 * i, 5.82 + .82 * i, member_shot(who, 1 if i % 2 == 0 else -1), trans=(3, .3))

    # ============================================================== 3. group (bars 9-11)
    def s_group(t, lt, d):
        k = kick(t)
        m.stage(uCurtain=1., uGrave=1., uMoon=1., uWall=(.22, .10, .035), uDeco=1., uCurtainCol=(.34, .05, .06),
                uSpot=[.14, .14, .13, 1, .36, .36, .13, 1, .56, .56, .13, 1, .76, .76, .13, 1],
                uSpotCol=[*CR, *CT, *CE, *CN])
        m.potatoes(potato_rain(t, B(9), B(11), 9, seed=5, face_p=.4), rim=(1, .6, .9))
        # everyone pops in from a different edge of the screen and settles into the line-up
        START = [(-520, -260), (960, -470), (W + 520, -260), (-560, H + 300), (W + 560, H + 300)]
        for j, who in m.cast():
            entrance = ease_out(clamp((t - B(9) - .06 * j) / .85), 3)
            ent = back_out((t - B(9) - .06 * j) / .95, 1.7)
            x_end = W * (.16 + .17 * j)
            hop = abs(math.sin(au.beats(t) * math.pi)) * 30 * (1 if j % 2 == (int(au.beats(t)) % 2) else .3)
            y_end = H * .66 - hop
            sx, sy = START[j]
            x = lerp(sx, x_end, ent); y = lerp(sy, y_end, ent)
            sc = lerp(.55, 1., entrance)
            m.l2d(who, x, y, 1120 * sc, smile=.7, uOutline=5, uOutlineColor=(1, 1, 1),
                  rot=(1 - entrance) * .6 * (1 if j % 2 else -1))
            # dust puff where each one lands (the tail shares Miku's slot, so no second puff)
            land = B(9) + .06 * j + .8
            if who != 'miku_tail' and 0 <= t - land < .5:
                m.parts(burst(t, land, (x_end, y_end + 220), 12, seed=60 + j, shape='circle',
                              colors=[(1, .95, .8), MCOL[who]], speed=(150, 420), size=(20, 46), g=300, life=.45,
                              outline=0., glow=.2, alpha=.55, fade=True))
        m.text('Wonderlands×Showtime', W / 2, H * .12, 80, font=m.at_serif, fill=(1, .85, .45), glow=.8,
               alpha=ease_out((t - B(9) - .5) / .3), outline=.15)
        return dict(uCA=.6 + k, uFlash=(1, 1, 1, .5 * math.exp(-max(0., t - B(10)) * 6)))

    add(9, 11, s_group, trans=(0, .5))

    # ============================================================== 4. spotlight potato (bar 11-12)
    def s_spot(t, lt, d):
        m.stage(uCurtain=1., uBulbs=.15, uWall=(.09, .035, .012), uGrave=.6, uMoon=.3, uHaze=.5, uDeco=.6,
                uSpot=[.5, .5, .14, 1., 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], uSpotCol=[1, .95, .8] + [0] * 9)
        p = [((0, -.35 + .03 * math.sin(t * 3), 1.5), .45, (0, 1, .2), math.sin(lt * 1.6) * .8, 7., 1.)]
        m.potatoes(p, rim=(1, .9, .7), key=(0, 1, .5))
        m.text('本日の演目', W / 2, H * .22, 60, font=m.at_serif, fill=(1, .9, .7), alpha=window(t, B(11.1), B(11.9), .3, .2))
        return dict(uVignette=1.2, uBloomAmt=.9)

    add(11, 12, s_spot, trans=(1, .3))

    # ============================================================== 5. TV verse (bars 12-16)
    TV_CONTENT = [('card', 'tsu_a'), ('card', 'rui_a'), ('spr', 'tsukasa', 58), ('noise',), ('card', 'miku'), ('spr', 'emu', 40),
                  ('stew_cold',), ('spr', 'tsukasa', 85)]

    def tv_screen(t, idx, lt):
        """render TV content #idx into m.tv_fbo"""
        prev = m.cur; m.cur = m.tv_fbo; m.tv_fbo.use(); m.ctx.clear(0, 0, 0, 1)
        W0, H0 = m.W, m.H; m.W, m.H = 960, 720
        c = TV_CONTENT[idx % len(TV_CONTENT)]
        if c[0] == 'card':
            m.cover(m.card[c[1]], zoom=1.15 + .04 * lt, pan=(math.sin(lt * .5) * .6, 0))
        elif c[0] == 'spr':
            m.comic(uColA=(.95, .9, .8), uColB=(.8, .7, .6), uMode=3., uFocus=(.5, .5))
            tex = m.sprite_tex(c[1], c[2])
            m.img(tex, 480, 400 + 10 * math.sin(lt * 9), 640, 640 * tex.height / tex.width)
        elif c[0] == 'stew_cold':
            m.stew(uColA=(.05, .1, .2), uColB=(.3, .45, .6), uColC=(.8, .9, 1.), uSwirl=.6, uBubble=.25, uHeat=0.)
        else:
            m.comic(uColA=(.2, .2, .2), uColB=(.6, .6, .6), uMode=1., uFocus=(.5, .5))
        m.W, m.H = W0, H0
        m.cur = prev; prev.use()

    def draw_tv(t, cx, cy, w, h, idx, lt, power=1., noise=0., channel=0., rot=0.):
        tv_screen(t, idx, lt)
        m.e.pass_('crt.frag', m.cur, {'uScreen': m.tv_tex}, blend=True, uTime=t, uCenter=(cx, cy), uSize=(w, h), uRot=rot,
                  uBody=(.42, .3, .22), uPower=power, uNoise=noise, uChannel=channel)

    def tv_index(t):
        Ls = [L for L in m.lyr.lines if L['section'] == 'verse1']
        i = 0
        for j, L in enumerate(Ls):
            if t >= L['start'] - .2: i = j
        return i, t - (Ls[i]['start'] - .2)

    def s_tv1(t, lt, d):
        m.comic(uColA=(.08, .04, .12), uColB=(.14, .07, .2), uMode=3., uFocus=(.5, .45))
        idx, llt = tv_index(t)
        zoom = 1.0 + .08 * ease_inout(lt / d)
        ch = math.exp(-llt * 12) if llt > 0 else 0
        draw_tv(t, W / 2, H * .45, 1100 * zoom, 800 * zoom, idx, llt, noise=.15 + .6 * ch, channel=.4 * ch)
        # APPLAUSE sign that never lights properly
        flick = .25 + .2 * (math.sin(t * 37) > .7)
        m.img(m.card['tsu_a'], W / 2, 70, 360, 80, uTint=(.25, .05, .05, 1.), uMask=1., uMaskRound=18)
        m.text('APPLAUSE', W / 2, 72, 52, fill=(1, .3, .3), line=(.2, 0, 0, 1), alpha=flick, glow=.3 * flick, tracking=.1)
        m.lyrics(t, style='tv', x=W / 2, y=H * .93, size=62, outline=.2, exit_mode='fade', hold=.15)
        return dict(uGrain=.08, uVignette=1.0, uSat=.9)

    add(12, 16, s_tv1, trans=(4, .6))

    # ============================================================== 6. TV wall (bars 16-21)
    def s_tv2(t, lt, d):
        k = kick(t)
        m.comic(uColA=(.1, .04, .14), uColB=(.2, .08, .26), uMode=2., uFocus=(.5, .5), uSpin=.1)
        idx, llt = tv_index(t)
        zoom = ease_out(lt / 1.0)
        cols, rows = 3, 3
        tw, th = 560, 400
        n = 0
        for r_ in range(rows):
            for c_ in range(cols):
                cx = W / 2 + (c_ - 1) * (tw + 40) * lerp(.6, 1., zoom)
                cy = H / 2 + (r_ - 1) * (th + 30) * lerp(.6, 1., zoom) - 30
                cidx = idx + n * 3 + int(au.bars(t) * 2) * (n % 2)
                if n == 4: cidx = idx
                ch = k if n != 4 else 0
                draw_tv(t, cx, cy, tw * (1 + .02 * k), th * (1 + .02 * k), cidx, llt + n, noise=.1 + .3 * ch, channel=.25 * ch,
                        rot=.02 * math.sin(n * 7.1))
                n += 1
        m.lyrics(t, style='pop', x=W / 2, y=H * .9, size=88, glow=.3, exit_mode='fall', hold=.15)
        return dict(uCA=.6 + 1.2 * k, uShake=(.002 * k, 0), uGrain=.06)

    add(16, 21, s_tv2, trans=(5, .35))

    # ============================================================== 7. TVs switch off (bar 21-22)
    def s_tvoff(t, lt, d):
        m.comic(uColA=(.03, .01, .05), uColB=(.08, .03, .1), uMode=3.)
        for n in range(9):
            cx = W / 2 + (n % 3 - 1) * 600; cy = H / 2 + (n // 3 - 1) * 430 - 30
            off_t = B(21) + n * au.beat * .45
            pw = 1 - clamp((t - off_t) / .25)
            draw_tv(t, cx, cy, 560, 400, n * 2, lt, power=pw, noise=.3)
        return dict(uVignette=1.1)

    add(21, 22, s_tvoff)

    # ============================================================== 8. pre-chorus 1 (bars 22-26)
    def s_pre1(t, lt, d):
        k = kick(t)
        build = clamp(lt / d)
        m.stage(uCurtain=1., uBulbs=.0, uWall=(.07, .03, .012), uGrave=0., uMoon=0., uHaze=1.,
                uSpot=[.28, .3, .16, 1., .72, .7, .16, 1., 0, 0, 0, 0, 0, 0, 0, 0], uSpotCol=[*CT, *CR, 0, 0, 0, 0, 0, 0])
        # floating mis-buttoned buttons
        rows = []
        for j in range(16):
            r = np.random.RandomState(j)
            x = r.uniform(0, W); y = (r.uniform(0, H) - t * r.uniform(20, 60)) % (H + 200) - 100
            s = r.uniform(40, 110)
            rows.append([x, y, s, s, t * r.uniform(-.8, .8) + j, 5, *[(.85, .75, .5), (.6, .5, .9), (.9, .5, .6)][j % 3], .55, .6, 0, 0, 0])
        m.parts(rows)
        if t < B(24.6):
            look = -1 if t > B(23) else 0
            m.l2d('tsukasa', W * .28, H * .62, 1300, motion='m-cool03-trouble', mphase=lt, head=(15, 0, 0), sweat=build)
            m.l2d('rui', W * .70, H * .62, 1300, motion='m-cool02-nod', mphase=lt * .5, head=(-15 + 25 * (look < 0), -5, 0),
                  look=(look, 0))
        else:
            lt2 = t - B(24.6)
            m.cover(m.card['rui_b'], zoom=1.2 + .25 * lt2, pan=(-.4, -.4), uDuo=.6, uDuoA=(.1, 0, .05), uDuoB=(1, .3, .35))
            m.img(m.crop['rui_b'], W * .5, H * .5, 900, 864, uOpacity=0)
        tb_style = dict(vertical=True, x=W * .42, y=110, size=78, glow=.4, maxw=820)
        m.lyrics(t, **tb_style)
        return dict(uSat=.7 + .4 * build, uVignette=1.2, uShake=(.004 * build * k, 0), uCA=.5 + 2 * build * k)

    add(22, 26, s_pre1, trans=(1, .4, (.5, .5)))

    # ============================================================== 9. calm before (bar 26-27)
    def s_stop1(t, lt, d):
        p = clamp(lt / d)
        m.stew(uColA=(.05, .02, .02), uColB=(.25 + .5 * p, .08 + .2 * p, .04), uColC=(.9, .6, .3), uSwirl=.2 + p, uBubble=.1 + .8 * p, uHeat=p,
               uZoom=1.6 - .6 * p)
        return dict(uVignette=1.4 - .6 * p, uFlash=(1, .85, .6, smooth((lt - d + .25) / .25)))

    add(26, 27, s_stop1)

    # ============================================================== 10. chorus (bars 27-38) / (65-78) shared
    def chorus_bg(t, bar, fire_mode):
        k = kick(t)
        hot = fire_mode
        colA = (.35, .06, .02) if not hot else (.4, .03, .01)
        colB = (.98, .47, .12) if not hot else (1., .35, .05)
        m.stew(uColA=colA, uColB=colB, uColC=(1, .88, .55), uSwirl=1.2 + .6 * (bar % 2), uBubble=.6 + .4 * k, uHeat=.5 + .5 * hot,
               uZoom=1.0 + .06 * k)

    def chorus_shot(first_bar, last_bar, fire_mode):
        def fn(t, lt, d):
            k = kick(t); s = snare(t)
            bar = int(au.bars(t)) - first_bar   # 0.. line index within the chorus
            bl = au.bars(t) - int(au.bars(t))
            Ls = [L for L in m.lyr.lines if L['section'] == ('chorus2' if fire_mode else 'chorus1')]
            cur = None
            for L in Ls:
                if t >= L['start'] - .15: cur = L
            txt = cur['text'] if cur else ''
            post = dict(uCA=.7 + 2. * k, uShake=(.003 * k * math.sin(t * 50), .004 * k), uBloomAmt=.9)
            chorus_bg(t, bar, fire_mode)
            # fire layer for chorus 2
            if fire_mode:
                hgt = .35 + .25 * k
                if '燃え上がって' in txt: hgt = .5 + .7 * smooth((t - cur['start']) / 1.2)
                if '薪' in txt: hgt = .35 + .4 * kick(t, 3)
                m.fire(height=hgt, intensity=.95)
            # --- content by line ---
            if 'potato' in txt:
                lt2 = t - cur['start']
                pot_t = [c['s'] for c in cur['chars'] if c['roma'] == 'po'][0]
                poof = t >= pot_t
                for j, who in m.cast():
                    x = W * (.14 + .18 * j); y = H * .6
                    if not poof:
                        m.l2d(who, x, y - 40 * abs(math.sin(au.beats(t) * math.pi)), 1050, smile=.8, uOutline=5, uOutlineColor=(1, 1, 1))
                pots = []
                if poof:
                    tau = t - pot_t
                    for j in range(len(ROSTER)):
                        wx, wy = world_xy(W * (.14 + .18 * j), H * .5, 1.2)
                        pots.append(((wx, wy + .25 * math.exp(-tau * 4) * math.sin(tau * 18), 1.2), .55 * back_out(tau / .3), (0, 1, .1),
                                     math.sin(tau * 6 + j) * .4 + 1.57 * 0, 3. + j, 1.))
                    m.potatoes(pots, rim=(1, .6, .3), glow=.5)
                    rows = []
                    for j in range(len(ROSTER)):
                        rows += burst(t, pot_t, (W * (.14 + .18 * j), H * .55), 16, seed=40 + j + bar, shape='circle',
                                      colors=[(1, 1, 1), (1, .95, .8)], speed=(200, 600), size=(40, 90), g=-200, life=.7, outline=0., glow=.3, alpha=.7, fade=True)
                    m.parts(rows)
                m.potatoes(potato_fountain(t, cur['start'], cur['end'] + .5, 10, (0, -2.2, -.5), seed=bar + 77, speed=(4, 6), spread=1.6))
            elif 'みんなで' in txt or 'どろどろ' in txt or 'そんな暮らし' in txt:
                sinking = 'どろどろ' in txt
                melt = smooth((t - cur['start']) / (cur['end'] - cur['start'] + .4)) if sinking else 0.
                BOWL = dict(cx=.5, cy=.24, rx=.82, ry=.25, glaze=(.2, .12, .3), stew=((.6, .2, .05), (1, .55, .15)))
                # nobody stands in the pot; the soup and the potatoes are the whole content
                cauldron(t, **BOWL, layer=2)
                cauldron(t, **BOWL, layer=0)
                m.potatoes(pot_floats(t, BOWL, seed=11 + bar, n=14, n_front=6), rim=(1, .55, .3), glow=.25)
                if melt > 0:
                    for j in range(5):
                        r = np.random.RandomState(bar * 31 + j)
                        rows = []
                        for q in range(6):
                            age = ((t * .7 + q / 6.) % 1.)
                            rows.append([W * (.2 + .6 * r.rand()), H * (.45 + .35 * age), 16 + 22 * age, 12 + 16 * age,
                                         0, 2, 1., .85, .55 + .3 * melt, .8 * (1 - age), 0, 0, 0, 0])
                        m.parts(rows)
                cauldron(t, **BOWL, layer=1)
            elif 'ボウル' in txt or '憂さ晴らし' in txt:
                lt2 = t - [L for L in Ls if 'ボウル' in L['text']][0]['start']
                rise = ease_out(lt2 / .8)
                cy = lerp(-.10, .36, rise)
                BOWL = dict(cx=.5, cy=cy - .12, rx=.84, ry=.25, glaze=(.95, .93, .9), stew=((.85, .4, .1), (1, .7, .3)))
                cauldron(t, **BOWL, layer=2)
                cauldron(t, **BOWL, layer=0)
                m.potatoes(pot_floats(t, BOWL, seed=29 + bar, n=14, n_front=6), rim=(1, .7, .35), glow=.25)
                if '憂さ' in txt:
                    # potatoes hop out of the bowl on the beat instead of the cast jumping
                    hop = abs(math.sin(au.beats(t) * math.pi))
                    pots = []
                    for j in range(7):
                        bx = -2.4 + j * .8
                        pots.append(((bx, .30 + hop * (.55 + .3 * math.sin(j * 2.1)), 1.1), .34, (0, 1, .3),
                                     math.sin(t * 3 + j) * .5, 40. + j, 1.))
                    m.potatoes(pots, rim=(1, .7, .35), glow=.35)
                cauldron(t, **BOWL, layer=1)                                  # near wall
            elif 'KUSHA' in txt:
                lt2 = t - cur['start']
                for j, who in m.cast():
                    r = np.random.RandomState(int(t * 12) + j)
                    m.l2d(who, W * (.1 + .2 * j) + r.uniform(-8, 8), H * .62 + r.uniform(-8, 8), 1080, smile=.5, eyes=.3,
                          rot=r.uniform(-.05, .05), uOutline=4, uOutlineColor=(1, 1, 1))
                cr = smooth((lt2 - .9) / 1.4)
                post.update(uCrumple=cr)
                end_t = B(last_bar + 2) if not fire_mode else B(last_bar + 1)
                throw = clamp((t - (end_t - .6)) / .6)
                post.update(uBallScale=1 - .75 * ease_in(throw), uBallOff=(.6 * ease_in(throw), -.4 * ease_in(throw)), uBallRot=throw * 3,
                            uBg=(.08, .03, .12))
            else:
                # panels: card art slams for single-subject lines; a small cast row sits at the bottom
                keys = [('tsu_a', 'emu_a'), ('rui_a', 'nen_a'), ('miku', 'tsu_b'), ('emu_b', 'rui_b'), ('tsu_a', 'miku'), ('nen_a', 'emu_a')]
                ka, kb = keys[(bar + (3 if fire_mode else 0)) % len(keys)]
                lt2 = t - (cur['start'] if cur else t)
                s1 = back_out(lt2 / .3); s2 = back_out((lt2 - au.beat * 2) / .3)
                if lt2 > 0:
                    m.img(m.card[ka], W * .3, H * .40, 900 * s1, 900 * s1 * (m.card[ka].height / m.card[ka].width), rot=-.06,
                          uOutline=12, uOutlineColor=(1, 1, 1), uShadow=1.)
                if lt2 > au.beat * 2:
                    m.img(m.card[kb], W * .7, H * .48, 900 * s2, 900 * s2 * (m.card[kb].height / m.card[kb].width), rot=.05,
                          uOutline=12, uOutlineColor=(1, 1, 1), uShadow=1.)
                m.potatoes(potato_rain(t, t - 3, t + 1, 3, seed=bar + 300, face_p=.2))
                for j, who in m.cast():
                    m.l2d(who, W * (.1 + .2 * j), H * 1.02, 1000, motion=BASE_MOTION[who], smile=.75, uOutline=5, uOutlineColor=MCOL[who])
            m.lyrics(t, x=W / 2, y=H * .86, size=112, style_fn=chorus_style, line=DARK, outline=.17, hold=.12)
            return post
        return fn

    add(27, 40, chorus_shot(27, 38, False), trans=(1, .25))

    # ============================================================== 11. interlude parade (bars 40-47)
    PARADE = ['rui_a', 'tsu_a', 'miku', 'emu_a', 'nen_a', 'rui_b', 'emu_b', 'miku']

    def s_parade(t, lt, d):
        k = kick(t)
        m.stage(uCurtain=1., uGrave=1., uMoon=1., uWall=(.21, .095, .033), uDeco=1., uCurtainCol=(.34, .05, .06),
                uSpot=[.15, .35 + .2 * math.sin(t), .2, .7, .85, .65 - .2 * math.sin(t), .2, .7, 0, 0, 0, 0, 0, 0, 0, 0],
                uSpotCol=[1, .5, .85, .5, .8, 1] + [0] * 6)
        bar = au.bars(t) - 40
        bi = int(bar)
        # scrolling strip of frames
        for j in range(-2, 3):
            idx = bi + j
            if idx < 0 or idx >= len(PARADE): continue
            off = j - (bar - bi) * 0 - ease_inout(clamp((bar - bi - .85) / .15))
            x = W / 2 + off * 1150
            sc = 1.0 if j == 0 else .8
            tex = m.card[PARADE[idx]]
            w = 1000 * sc * (1 + .03 * k * (j == 0)); h = w * tex.height / tex.width
            m.img(tex, x, H * .45, w, h, rot=.03 * math.sin(t * 1.3 + j), uOutline=14, uOutlineColor=(1, .8, .35), uShadow=1.,
                  uDesat=.0 if j == 0 else .5)
        # bouncing jack-o'-potatoes along the bottom
        pots = []
        for j in range(7):
            bx = (-3.0 + j * 1.0)
            hop = abs(math.sin((au.beats(t) + j * .5) * math.pi)) * .5
            pots.append(((bx, -1.55 + hop, 0.), .32, (0, 1, 0), math.sin(t * 3 + j) * .5, j + 11., 1.))
        m.potatoes(pots, rim=(1, .5, .2), glow=.4 * k)
        m.parts(drift(t, 18, 8, 'bat', [(.08, .03, .12)], size=(40, 80), vy=(-50, -20), sway=120, spin=.2))
        return dict(uCA=.6 + 1.2 * k, uBloomAmt=.8)

    add(40, 47, s_parade, trans=(3, .4))

    # ============================================================== 12. countdown (bar 47-48)
    def s_count(t, lt, d):
        m.comic(uColA=(.95, .85, .2), uColB=(.85, .3, .1), uMode=2., uSpin=1.5)
        n = 3 - int(au.beats(t) - au.beats(B(47)))
        bp = au.beat_phase(t)
        if n >= 1:
            m.text(str(n), W / 2, H * .5, 520 * back_out(bp / .25), fill=(1, 1, 1), line=DARK, outline=.12)
        else:
            m.text('ON AIR', W / 2, H * .5, 240 * back_out(bp / .25), fill=(1, .25, .3), outline=.12, glow=.6)
        m.text('残り時間', W / 2, H * .16, 70, fill=(.1, .05, .1), line=(1, 1, 1, 1), outline=.2)
        return dict(uHalftone=.25, uCA=1.)

    add(47, 48, s_count, trans=(4, .2))

    # ============================================================== 13. verse 2: the show contest (bars 48-56)
    def s_contest(t, lt, d):
        k = kick(t)
        m.stage(uCurtain=1., uGrave=0., uMoon=0., uWall=(.13, .06, .022), uBulbs=1.,
                uSpot=[.5, .5, .2, 1. + .5 * k, .2, .3, .14, .6, .8, .7, .14, .6, 0, 0, 0, 0], uSpotCol=[1, .9, .6, *CE, *CN, 0, 0, 0])
        Ls = [L for L in m.lyr.lines if L['section'] == 'verse2']
        cur = None
        for L in Ls:
            if t >= L['start'] - .15: cur = L
        li = Ls.index(cur) if cur else 0
        # scoreboard
        m.img(m.card['tsu_b'], W / 2, 95, 760, 130, uTint=(.06, .02, .1, 1.), uMask=1., uMaskRound=24, uOutline=6, uOutlineColor=(1, .8, .3))
        m.text('SHOW CONTEST', W / 2, 95, 70, fill=(1, .85, .35), glow=.6 * (.5 + .5 * math.sin(t * 6)), tracking=.08)
        # performers
        spin = 0.0
        if cur and '空回って' in cur['text']:
            ct = [c for c in cur['chars'] if c['t'] == '空'][0]['s']
            spin = ease_inout((t - ct) / .9) * math.pi * 4
        melt = 0.
        if cur and 'バター' in cur['text']:
            melt = smooth((t - cur['start']) / 2.2)
        m.l2d('tsukasa', W * .5, H * .62, 1250, motion='m-proud07-plan', mphase=t - B(48), rot=spin, smile=.5,
              uOutline=6, uOutlineColor=(1, .85, .3), uMelt=melt * .7, uTint=(1, 1 - .1 * melt, 1 - .7 * melt, .45 * melt))
        # the two backing singers slide in once and stay for the rest of the verse
        ent = ease_out((t - (Ls[4]['start'] - 1.2)) / .45)
        if ent > 0:
            for who, x0, mot in (('emu', W * .19, 'w-adult02-glad'), ('nene', W * .81, 'w-pure03-sigh')):
                m.l2d(who, x0 - (1 - ent) * 480 * (1 if who == 'emu' else -1), H * .66, 1100, motion=mot,
                      mphase=t - (Ls[4]['start'] - 1.2), smile=.8 if who == 'emu' else .2,
                      uOutline=5, uOutlineColor=MCOL[who], uMelt=melt * .6,
                      uTint=(1, 1 - .1 * melt, 1 - .3 * melt, .25 * melt))
        # booing -> medals
        boo_t = Ls[2]['start']; medal_t = [c for c in Ls[3]['chars'] if c['t'] == '勲'][0]['s']
        rows = []
        if boo_t - .2 < t < Ls[5]['start']:
            for j in range(26):
                r = np.random.RandomState(j + 500)
                st = boo_t + r.uniform(0, 1.2)
                tau = t - st
                if tau < 0: continue
                x = r.uniform(80, W - 80); y = -80 + tau * r.uniform(250, 420) + 20 * math.sin(tau * 4 + j)
                is_medal = t > medal_t + r.uniform(0, .25)
                sh = 7 if is_medal else 6
                col = [CR, CT, CE, CN][j % 4] if is_medal else (.45, .4, .55)
                s = r.uniform(60, 100) * (1 + .3 * math.exp(-(t - medal_t) * 6) * is_medal)
                rows.append([x, y, s, s, math.sin(tau * 3 + j) * .4, sh, *col, 1., 1., .6 * is_medal, 0, 0])
            if t > medal_t:
                rows += burst(t, medal_t, (W / 2, H * .4), 40, seed=9, shape='star', colors=[(1, .85, .3), (1, 1, 1)], speed=(400, 1300), life=1.3, glow=.6)
        m.parts(rows)
        if boo_t < t < medal_t:
            m.text('BOO!', W * .25, H * .3, 140, fill=(.6, .55, .7), rot=-.2, alpha=.8 * window(t, boo_t + .2, medal_t - .1, .2, .1))
            m.text('BOO!', W * .76, H * .38, 110, fill=(.6, .55, .7), rot=.18, alpha=.8 * window(t, boo_t + .5, medal_t - .1, .2, .1))
        m.lyrics(t, x=W / 2, y=H * .9, size=96, style_fn=lambda L: dict(), line=DARK, glow=.4, hold=.1)
        return dict(uCA=.6 + 1.4 * k, uShake=(0, .003 * k))

    add(48, 56, s_contest, trans=(0, .45))

    # ============================================================== 14. manga montage (bars 56-60)
    def s_montage(t, lt, d):
        k = kick(t)
        bt = au.beats(t) - au.beats(B(56))
        bi = int(bt)
        who = ORDER[bi % 4]
        c = MCOL[who]
        m.comic(uColA=(1, 1, 1), uColB=(.1, .05, .15), uMode=0., uFocus=(.5, .5))
        # last 3 panels stay visible, newest on top
        for j in range(max(0, bi - 2), bi + 1):
            w2 = ORDER[j % 4]
            tex = m.sprite_tex(w2, (j * 7 + 3) % 40)
            ap = back_out((bt - j) / .25)
            r = np.random.RandomState(j)
            x = W * (.2 + .6 * r.rand()); y = H * (.35 + .3 * r.rand())
            w = 560 * ap
            m.img(tex, x, y, w, w * tex.height / tex.width, rot=r.uniform(-.15, .15), uOutline=10, uOutlineColor=(0, 0, 0),
                  uHalftone=.4, uShadow=1., uMask=1., uMaskRound=8)
        m.text(['ドン!', 'バン!', 'ワッ!', '!?'][bi % 4], W * (.8 if bi % 2 else .2), H * .2, 160 * back_out((bt - bi) / .2), fill=c, rot=.2 * (1 if bi % 2 else -1), outline=.14)
        return dict(uHalftone=.15, uCA=1 + 1.5 * k, uShake=(.004 * k, .003 * k))

    add(56, 60, s_montage, trans=(5, .3))

    # ============================================================== 15. pre-chorus 2: memories (bars 60-64)
    def s_memory(t, lt, d):
        p = clamp(lt / d)
        m.stage(uCurtain=1., uBulbs=0., uWall=(.10, .09, .07), uGrave=0., uMoon=0., uHaze=1.5,
                uSpot=[.5, .5, .25, .5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], uSpotCol=[.7, .85, 1.] + [0] * 9)
        # memory photo of the SEKAI members
        ph = ease_out(lt / 1.)
        m.img(m.card['miku'], W * .62, H * .38, 820 * ph, 460 * ph, rot=.05, uOutline=16, uOutlineColor=(.95, .95, .9), uShadow=1.,
              uDesat=.6, uOpacity=.85)
        m.img(m.card['rui_a'], W * .36, H * .3, 640 * ph, 394 * ph, rot=-.08, uOutline=14, uOutlineColor=(.95, .95, .9), uShadow=1.,
              uDesat=.8, uOpacity=clamp((lt - 1.2) / .5))
        m.l2d('rui', W * .5, H * .78, 1000, motion='m-normal13-nod', mphase=lt * .4, head=(0, -18, 0), look=(0, -.6), eyes=.55,
              energy=.15, sing=True, uOutline=3, uOutlineColor=(.7, .85, 1.))
        # rain of memories
        rows = []
        for j in range(120):
            r = np.random.RandomState(j + 900)
            x = r.uniform(0, W); y = (r.uniform(0, H) + t * r.uniform(700, 1100)) % (H + 40) - 20
            rows.append([x, y, 3, 26, .1, 2, .7, .8, 1., .35, 0, 0, 0, 0])
        m.parts(rows)
        m.lyrics(t, vertical=True, x=W * .08, y=110, size=76, glow=.5, maxw=760)
        flash = smooth((lt - d + .5) / .5)
        return dict(uMono=.75 * (1 - flash), uSat=.8, uGrain=.07, uVignette=1.1, uFlash=(1, 1, 1, flash * .9))

    add(60, 64, s_memory, trans=(4, .8))

    # ============================================================== 16. the spark (bar 64-65)
    def s_spark(t, lt, d):
        p = clamp(lt / d)
        m.comic(uColA=(.02, .01, .02), uColB=(.05, .02, .03), uMode=3.)
        m.fire(height=.05 + .5 * ease_in(p), intensity=.6 + .4 * p)
        m.text('薪', W / 2, H * .45, 160 + 220 * ease_in(p), font=m.at_serif, fill=(1, .7, .3), glow=1., alpha=window(t, B(64.15), B(65), .1, .05))
        rows = burst(t, B(64.05), (W / 2, H * .9), 30, seed=3, shape='circle', colors=[(1, .7, .2), (1, .4, .1)], speed=(100, 500), g=-300, size=(6, 14), life=1.5, outline=0, glow=1.)
        m.parts(rows, additive=True)
        return dict(uVignette=1.2, uFlash=(1, .7, .4, smooth((lt - d + .2) / .2)))

    add(64, 65, s_spark)
    add(65, 79, chorus_shot(65, 78, True), trans=(1, .25))

    # ============================================================== 17. curtain call (bars 79-89)
    def s_call(t, lt, d):
        k = kick(t)
        bar = au.bars(t) - 79
        m.stage(uCurtain=1., uGrave=1., uMoon=1., uWall=(.22, .10, .035), uDeco=1., uCurtainCol=(.34, .05, .06),
                uSpot=[.2, .2, .14, 1, .4, .4, .14, 1, .6, .6, .14, 1, .8, .8, .14, 1], uSpotCol=[*CT, *CE, *CN, *CR])
        # rocket potato with a star (Rui's next contraption)
        if 3 < bar < 6.5:
            tau = (bar - 3) * au.bar_len
            x = -3.9 + tau * 1.25; y = .55 + tau * .22 + .08 * math.sin(tau * 8)
            m.potatoes([((x, y, 0.5), .42, (0, 0, 1), -.5, 5., 1.)], rim=(1, .7, .3), glow=1.)
            sx, sy = screen_xy(x, y, .5)
            rows = []
            for j in range(40):
                r = np.random.RandomState(j * 13 + int(t * 30))
                age = r.uniform(0, .6)
                rows.append([sx - 70 - age * 600 + r.uniform(-15, 15), sy + 20 + age * 250 + r.uniform(-25, 25), 30 * (1 - age), 30 * (1 - age),
                             0, 0, 1, .55 + .4 * (1 - age), .2, .9 * (1 - age / .6), 0, 1., 0, 0])
            m.parts(rows, additive=True)
        bow = clamp((bar - 1.5) / .5) * (1 - clamp((bar - 3) / .5))
        for j, who in m.cast():
            nod = bow * 25
            m.l2d(who, W * (.16 + .17 * j), H * .64, 1120, motion=BASE_MOTION[who], head=(0, -nod, 0), body=(0, -bow * 10, 0), smile=.9,
                  eyes=1 - .6 * bow, uOutline=5, uOutlineColor=(1, 1, 1))
        # third place medal
        if 1 < bar < 4.8:
            mp = back_out((bar - 1) / .4) * (1 - smooth((bar - 4.4) / .4))
            mr = [[W / 2, H * .13, 170 * mp, 170 * mp, math.sin(t * 2) * .15, 7, *CT, 1., 1., .8, 0, 0]]
            m.parts(mr)
            m.text('3RD PLACE', W / 2, H * .25, 58 * mp, fill=(1, .85, .35), glow=.6, alpha=clamp(mp))
        # credits
        creds = [(5, 'potatoになっていく', 84, .17), (6, '作詞・作曲・編曲  Neru', 46, .27),
                 (7, '歌  ワンダーランズ×ショウタイム × 初音ミク', 44, .335), (8, 'MV Opus5.5', 32, .455)]
        for b0, txt, sz, yy in creds:
            a = window(bar, b0, 10.3, .3, .3)
            if a > 0:
                m.text(txt, W / 2, H * yy, sz, font=m.at_serif, fill=(1, .92, .7), alpha=a, glow=.35, outline=.14)
        m.parts(drift(t, 70, 12, ['confetti', 'star', 'confetti'], [CR, CT, CE, CN, MEMBER['miku']], size=(14, 30), vy=(90, 200), sway=60, spin=3))
        return dict(uCA=.5 + k, uBloomAmt=.85)

    add(79, 89, s_call, trans=(0, .6))

    # ============================================================== 18. end (bar 89 - end)
    def s_end(t, lt, d):
        close = ease_inout((lt - 1.1) / 1.9)
        m.stage(uCurtain=1 - close, uGrave=1., uMoon=1., uWall=(.20, .09, .03), uDeco=1., uCurtainCol=(.34, .05, .06),
                uBulbs=1 - .7 * clamp((lt - 1.6) / 1.5),
                uSpot=[.5, .5, .2, 1 - close, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], uSpotCol=[1, .9, .7] + [0] * 9)
        pz = 2.2 if close > .02 else 1.0      # in front of the back wall, behind the closing curtains
        m.potatoes([((0, .05 * math.sin(lt * 2.), pz), .62 * (1 - close * .15), (0, 1, 0), t * .6, 14., 1.)], rim=(1, .8, .5))
        # the closing curtains pass in front of everything on stage ...
        m.bg('stage.frag', blend=True, uCurtainOnly=1., uCurtain=1 - close, uCurtainCol=(.34, .05, .06))
        a = clamp((lt - 1.2) / .5)
        m.text('おしまい', W / 2, H * .80, 150, font=m.at_serif, fill=(1, .85, .45), glow=.8, alpha=a)
        return dict(uFlash=(0, 0, 0, smooth((lt - 2.6) / .7)))

    add(89, 91, s_end, t1=au.dur + 1)
    return shots
