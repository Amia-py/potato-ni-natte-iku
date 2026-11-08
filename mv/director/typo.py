"""Showbill typography.

The look of this MV is carried by type, not by the picture: a printed page, a hairline
frame, technical read-outs in the margins, and display words big enough to be cropped by
the frame. This module owns that furniture so the shots stay short.
"""
import math
import numpy as np
from engine.text import layout, TextBatch
from .common import clamp, smooth, ease_out, ease_in, ease_inout, lerp

# ---- spot inks (1970s film print: aged paper, lamp amber, rust, bottle teal) ----
PAPER  = (.906, .875, .784)
INK    = (.106, .086, .067)
GRAY   = (.44, .40, .34)
YELLOW = (.80, .48, .16)    # amber lamp
PINK   = (.70, .28, .22)    # rust
GREEN  = (.20, .38, .36)    # bottle teal
PURPLE = (.42, .26, .28)    # faded plum
TEAL   = (.18, .34, .36)
CREAM  = (.960, .932, .862)
GOLD   = (.86, .70, .38)

SMALL = set('っゃゅょぁぃぅぇぉャュョァィゥェォッ々')


def _punct_off(ch):
    """vertical writing: punctuation hugs the top-right of its cell"""
    return (0.30, -0.26) if ch in '、。，．' else (0., 0.)


def _vglyph(m, ch, x, cy, size, font, fill, alpha, outline=0., rot=0., line=(0, 0, 0, 1), tb=None):
    own = tb is None
    tb = tb or TextBatch()
    dx, dy = _punct_off(ch)
    gx, gy, r = x + dx * size, cy + dy * size, rot
    if ch in SMALL:
        gx += size * .11; gy -= size * .11
    elif ch in 'ー〜―':
        r = math.pi / 2
    elif ch.isascii() and ch.isalpha():
        r = math.pi / 2
    tb.glyph(font, ch, gx, gy, size, r, fill=(*fill, 1), fill2=(*fill, 1), line=line,
             outline=outline, alpha=alpha)
    if own:
        m.flush(tb, font)


def vcol(m, s, x, y, size, font=None, fill=INK, leading=1.58, alpha=1., outline=0., tb=None, line=(0, 0, 0, 1)):
    """one vertical column; y is the top edge of the first cell"""
    font = font or m.f_serif
    own = tb is None
    tb = tb or TextBatch()
    for i, ch in enumerate(s):
        _vglyph(m, ch, x, y + size * .5 + i * size * leading, size, font, fill, alpha, outline, tb=tb, line=line)
    if own:
        m.flush(tb, font)
    return len(s) * size * leading


def htext(m, s, x, y, size, font=None, fill=INK, align='left', tracking=.0, alpha=1., outline=0., rot=0., tb=None):
    font = font or m.f_dot
    own = tb is None
    tb = tb or TextBatch()
    xs, w = layout(font, s, size, tracking)
    x0 = x - w / 2 if align == 'center' else (x if align == 'left' else x - w)
    c, sn = math.cos(rot), math.sin(rot)
    for ch, gx in zip(s, xs):
        dx = x0 + gx - x
        tb.glyph(font, ch, x + dx * c, y + dx * sn, size, rot, fill=(*fill, 1), fill2=(*fill, 1),
                 line=(0, 0, 0, 1), outline=outline, alpha=alpha)
    if own:
        m.flush(tb, font)
    return w


def micro(m, s, x, y, size=14, font=None, fill=INK, align='left', tracking=.14, alpha=.55, tb=None):
    return htext(m, s, x, y, size, font or m.f_mono, fill, align, tracking, alpha, tb=tb)


def readout(m, t, bar, dur, ink=INK, alpha=.5, y=38):
    """the printed spec strip: unit name on the left, BPM / bar / timecode on the right"""
    W = m.W
    mm, ss = divmod(max(t, 0.), 60.)
    micro(m, 'WONDERLANDS×SHOWTIME  /  POTATO-NI-NATTEIKU', 86, y, 14, fill=ink, tracking=.18, alpha=alpha)
    micro(m, f'116 BPM   BAR {bar:05.1f}   {int(mm):02d}:{ss:05.2f}', W - 86, y, 14, fill=ink,
          align='right', tracking=.16, alpha=alpha)


def page_no(m, no, total, ink=INK, alpha=.45, y=None):
    W, H = m.W, m.H
    y = y if y is not None else H - 46
    micro(m, f'{no:02d} / {total:02d}', W - 86, y, 14, fill=ink, align='right', tracking=.2, alpha=alpha)
    micro(m, 'ALL RIGHTS RESERVED  ·  PRINTED IN SEKAI', 86, y, 12, fill=ink, tracking=.16, alpha=alpha * .8)


def display(m, s, x, y, size, font=None, fill=INK, rot=0., align='center', tracking=-.02,
            alpha=1., outline=0., jitter=0., seed=0, tb=None, per_glyph=None, pulse=True):
    """oversized word; jitter rotates each glyph a little so it reads as set, not typed"""
    font = font or m.f_round
    own = tb is None
    tb = tb or TextBatch()
    xs, w = layout(font, s, size, tracking)
    x0 = x - w / 2 if align == 'center' else (x if align == 'left' else x - w)
    c, sn = math.cos(rot), math.sin(rot)
    # a display word never sits perfectly still: it takes the kick on the plate
    if pulse:
        size *= 1. + .016 * m.au.pulse(m.t, 'kick', 9.)
    for i, (ch, gx) in enumerate(zip(s, xs)):
        dx = x0 + gx - x
        r = rot + (np.random.RandomState(seed * 31 + i).uniform(-jitter, jitter) if jitter else 0.)
        px, py = x + dx * c, y + dx * sn
        if per_glyph: px, py = per_glyph(i, px, py)
        tb.glyph(font, ch, px, py, size, r, fill=(*fill, 1), fill2=(*fill, 1), line=(0, 0, 0, 1),
                 outline=outline, alpha=alpha)
    if own:
        m.flush(tb, font)
    return w


def glyph_field(m, t, seed, n, box, sizes=(18, 90), colors=(INK,), alpha=.5, font=None, drift=0.,
                tb=None):
    """text as texture: a scatter of small glyphs, the printed-noise layer"""
    font = font or m.f_pop
    x0, y0, x1, y1 = box
    r = np.random.RandomState(seed)
    chars = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
    own = tb is None
    tb = tb or TextBatch()
    for i in range(n):
        ch = chars[int(r.randint(0, len(chars)))]
        sx = x0 + r.rand() * (x1 - x0)
        sy = y0 + r.rand() * (y1 - y0)
        sz = sizes[0] + r.rand() * (sizes[1] - sizes[0])
        rot = r.uniform(0, math.pi * 2)
        a = alpha * (.35 + .65 * r.rand())
        if drift:
            sx += math.sin(t * (.6 + r.rand()) + i) * drift
            sy += math.cos(t * (.5 + r.rand()) + i * 1.7) * drift
        col = colors[int(r.randint(0, len(colors)))]
        tb.glyph(font, ch, sx, sy, sz, rot, fill=(*col, 1), fill2=(*col, 1), line=(0, 0, 0, 1), alpha=a)
    if own:
        m.flush(tb, font)


def lyric_v(m, L, t, x, y, size, font=None, leading=1.52, ink=INK, accent=None, alpha=1., maxc=None, dim=.16):
    """vertical lyric column with the print-progress: unsung glyphs sit at low ink,
    sung ones come up to full black, the newest one is stamped in the accent ink."""
    font = font or m.f_serif
    tb = TextBatch()
    gl = L['glyphs']
    if maxc: gl = gl[:maxc]
    for i, g in enumerate(gl):
        s, e = g['s'], g['e']
        if e > s:
            up = clamp((t - s) / (e - s))
            sweep = clamp(up * g['n'] - g['k'])
        else:
            sweep = 1. if t >= s else 0.
        a = alpha * (dim + (1. - dim) * smooth(sweep * 1.6))
        col = ink
        if accent and 0. < sweep < .999:
            col = accent
        cy = y + size * .5 + i * size * leading
        _vglyph(m, g['ch'], x, cy, size, font, col, a, tb=tb)
    m.flush(tb, font)


def stamp(m, cx, cy, r, s, t, ink=INK, alpha=.8, size=15, font=None, rot=0., tb=None):
    """round rubber stamp: text set on the circle, plus a rule ring"""
    font = font or m.f_mono
    own = tb is None
    tb = tb or TextBatch()
    n = len(s)
    span = math.pi * 2 * .78
    for i, ch in enumerate(s):
        a = rot - span / 2 + span * (i / max(n - 1, 1))
        px = cx + math.sin(a) * r
        py = cy - math.cos(a) * r
        tb.glyph(font, ch, px, py, size, a, fill=(*ink, 1), fill2=(*ink, 1), line=(0, 0, 0, 1), alpha=alpha)
    if own:
        m.flush(tb, font)
