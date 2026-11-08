"""Per-character karaoke lyric rendering with several kinetic styles.

Each glyph is coloured by its SEKAI singer credit (see singers in lyrics_timing.json):
with several singers on a line the colours alternate glyph by glyph, sung glyphs are
brightened, not-yet-sung / non-singing characters are dimmed.
"""
import json, math
import numpy as np
from engine.text import layout
from .common import clamp, smooth, back_out, ease_in, ease_out, lerp, WORK

MEMBER = {'tsukasa': (1.0, .76, .15), 'emu': (1.0, .42, .72), 'nene': (.25, .88, .6), 'rui': (.72, .52, .95),
          'miku': (.24, .80, .87), 'potato': (.92, .72, .40), 'white': (1, 1, 1), 'stew': (1, .52, .16)}
SINGER_KEY = {'神代類': 'rui', '天馬司': 'tsukasa', '鳳えむ': 'emu', '草薙寧々': 'nene', '初音ミク': 'miku'}
SMALL = set('っゃゅょぁぃぅぇぉャュョァィゥェォッ')


def brighten(c, k):
    return tuple(min(1.0, x * k + (k - 1) * .35) for x in c)


def dim(c, k=.5):
    return tuple(x * k for x in c)


class Lyrics:
    def __init__(self, atlas):
        self.at = atlas
        self.lines = json.load(open(f'{WORK}/lyrics_timing.json', encoding='utf-8'))
        for li, L in enumerate(self.lines):
            g = []; prev_e = L['start']
            for ui, c in enumerate(L['chars']):
                s, e = c['s'], c['e']
                if s is None: s, e = prev_e, prev_e
                prev_e = e
                n = len(c['t'])
                for k, ch in enumerate(c['t']):
                    g.append(dict(ch=ch, ui=ui, k=k, n=n, s=s, e=e,
                                  potato=c['roma'] in ('po', 'te', 'to') and c['t'].isascii(),
                                  sep=c['s'] is None, unit_text=c['t']))
            L['glyphs'] = g
            L['idx'] = li
            L['colors'] = [MEMBER.get(SINGER_KEY[s], MEMBER['white']) for s in L.get('singers', [])] or [MEMBER['white']]
        for a, b in zip(self.lines, self.lines[1:]):
            a['next_start'] = b['start']
        self.lines[-1]['next_start'] = 1e9

    def chars(self):
        s = set()
        for L in self.lines:
            for c in L['chars']:
                s |= set(c['t'])
        return s

    def active(self, t, pre=.5, post=.6):
        return [L for L in self.lines if L['start'] - pre <= t <= L['end'] + post]

    # ------------------------------------------------------------------
    def draw_line(self, tb, L, t, style='pop', x=960, y=860, size=110, maxw=1700, color=None, color2=None,
                  line=(.08, .03, .12, 1), outline=.16, glow=.0, alpha=1.0, exit_mode='fall', hold=.35,
                  align='center', tracking=0.0, vertical=False, pre=.25, dim_unsung=.62):
        at = self.at
        gl = L['glyphs']
        colors = L['colors']
        if vertical:
            return self._draw_vertical(tb, L, t, x, y, size, line, outline, glow, alpha, hold, colors, maxw, pre)
        # potato glyphs are rendered bigger: compute widths with per-glyph scale
        scales = [1.55 if (g['potato'] and style in ('pop', 'potato')) else 1.0 for g in gl]
        advs = [at.adv(g['ch']) * size * sc for g, sc in zip(gl, scales)]
        total = sum(advs) + tracking * size * (len(gl) - 1)
        k = min(1.0, maxw / max(total, 1))
        size *= k; advs = [a * k for a in advs]; total *= k
        x0 = x - total / 2 if align == 'center' else (x if align == 'left' else x - total)
        cx = x0; lend = L['end']
        for i, (g, sc, a) in enumerate(zip(gl, scales, advs)):
            gx = cx + a / 2; cx += a + tracking * size
            s, e = g['s'], g['e']
            # karaoke progress within the glyph
            if e > s:
                up = clamp((t - s) / (e - s)); sweep = clamp(up * g['n'] - g['k'])
            else:
                sweep = 1.0 if t >= s else 0.0
            gs = size * sc
            gy = y; rot = 0.0; a_ = alpha; scl = 1.0
            if style == 'tv':
                if t < s - .02: continue   # typewriter
                a_ *= smooth((t - s + .02) / .06)
                sweep = 1.0
            elif style in ('pop', 'potato', 'shake'):
                ap = (t - (s - pre * .4)) / .22
                if ap < 0: continue
                scl = back_out(ap, 2.6) if ap < 1 else 1.0
                rot = (1 - clamp(ap)) * (.5 if i % 2 else -.5)
                if g['potato']:
                    bounce = math.sin(clamp((t - s) / .25) * math.pi) * .25
                    scl *= 1 + bounce; gy -= bounce * gs * .5
                if style == 'shake' and t > s:
                    r = np.random.RandomState(int(t * 15) * 97 + i)
                    rot += r.uniform(-.25, .25); gx += r.uniform(-6, 6); gy += r.uniform(-6, 6)
            # exit
            te = min(lend + hold, L['next_start'] - .3)
            if t > te:
                tau = t - te - i * .015
                if tau > 0:
                    if exit_mode == 'fall':
                        r = np.random.RandomState(L['idx'] * 1000 + i)
                        gy += 1400 * tau * tau + r.uniform(-60, 60) * tau
                        gx += r.uniform(-200, 200) * tau
                        rot += r.uniform(-4, 4) * tau
                        a_ *= 1 - smooth(tau / .5)
                    else:
                        a_ *= 1 - smooth(tau / .3)
            if a_ <= 0.01: continue
            base = colors[i % len(colors)] if color is None else color
            if color2 is not None: base2 = color2
            else: base2 = brighten(base, 1.25) if len(colors) > 1 else tuple(min(1., x + .25) for x in base)
            if g['potato']:
                base = MEMBER['potato']; base2 = (1.0, .9, .55)
            # dim what has not been sung yet, and characters nobody sings
            if sweep <= 0.01:
                base = dim(base, dim_unsung); base2 = dim(base2, dim_unsung)
            if not L.get('singers'):
                base = dim(base, .8); base2 = dim(base2, .8)
            tb.glyph(at, g['ch'], gx, gy, gs * scl, rot, fill=(*base, 1), fill2=(*base2, 1), line=line,
                     outline=outline, glow=glow * (sweep > 0), sweep=sweep, alpha=a_)

    def _draw_vertical(self, tb, L, t, x, y, size, line, outline, glow, alpha, hold, colors, maxw, pre):
        at = self.at
        gl = L['glyphs']
        n_rows = max(1, int((maxw) / size))            # characters per column
        col_w = size * 1.06
        n_cols = (len(gl) + n_rows - 1) // n_rows
        x_right = x + n_cols * col_w                 # columns run right -> left
        for i, g in enumerate(gl):
            s, e = g['s'], g['e']
            col = i // n_rows; row = i % n_rows
            gx = x_right - col * col_w - size * .5
            gy = y + row * size + size * .5
            if t < s - .1: continue
            a_ = alpha * smooth((t - s + .1) / .15)
            if e > s: sweep = clamp(clamp((t - s) / (e - s)) * g['n'] - g['k'])
            else: sweep = 1.0
            te = L['end'] + hold
            if t > te: a_ *= 1 - smooth((t - te) / .4)
            if a_ <= .01: continue
            ch = g['ch']; rot = 0.0
            if ch in SMALL: gx += size * .13; gy -= size * .13
            if ch in 'ー〜': rot = math.pi / 2
            if ch.isascii() and ch.isalpha(): rot = math.pi / 2
            base = colors[i % len(colors)]; base2 = brighten(base, 1.3) if len(colors) > 1 else base
            if ch in ' 、': a_ *= .3
            if sweep <= .01: base = dim(base, .62); base2 = dim(base2, .62)
            slide = (1 - ease_out((t - s + .1) / .25)) * 40
            tb.glyph(at, ch, gx + slide, gy, size, rot, fill=(*base, 1), fill2=(*base2, 1), line=line, outline=outline,
                     glow=glow * (sweep > 0), sweep=sweep, alpha=a_)
