"""SDF glyph atlases (PIL + scipy EDT) and instanced text rendering."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt
import moderngl

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fonts')

FONTS = {
    'jp_black': ('C:/Windows/Fonts/NotoSansJP-VF.ttf', 900),
    'jp_bold': ('C:/Windows/Fonts/NotoSansJP-VF.ttf', 700),
    'serif_black': ('C:/Windows/Fonts/NotoSerifJP-VF.ttf', 900),
    'serif': ('C:/Windows/Fonts/NotoSerifJP-VF.ttf', 350),
    'latin': ('C:/Windows/Fonts/ariblk.ttf', None),
    # showbill faces: rounded pop for display, dot matrix for printed micro type
    'pop': (os.path.join(FONT_DIR, 'MochiyPopOne-Regular.ttf'), None),
    'round': (os.path.join(FONT_DIR, 'RocknRollOne-Regular.ttf'), None),
    'dot': (os.path.join(FONT_DIR, 'DotGothic16-Regular.ttf'), None),
    'decol': (os.path.join(FONT_DIR, 'KaiseiDecol-Bold.ttf'), None),
    'mono': ('C:/Windows/Fonts/consola.ttf', None),
}
S = 128          # glyph render size (px)
P = 22           # padding / sdf spread region
CELL = S + 2 * P
SPREAD = 18.0


def _font(key):
    path, wght = FONTS[key]
    f = ImageFont.truetype(path, S)
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


class Atlas:
    def __init__(self, eng, key, chars, cache_dir):
        self.key = key
        os.makedirs(cache_dir, exist_ok=True)
        chars = sorted(set(chars) - {' ', '\n'})
        png, meta = os.path.join(cache_dir, f'atlas_{key}.png'), os.path.join(cache_dir, f'atlas_{key}.json')
        m = json.load(open(meta, encoding='utf-8')) if os.path.exists(meta) else None
        if m is None or set(chars) - set(m['glyphs']):
            self._build(chars, png, meta)
            m = json.load(open(meta, encoding='utf-8'))
        self.glyphs = m['glyphs']; self.cols = m['cols']; self.size = m['size']
        self.ascent = m['ascent']; self.descent = m['descent']
        im = Image.open(png)
        a = np.asarray(im)[::-1].copy()
        self.tex = eng.ctx.texture(im.size, 1, a.tobytes())
        self.tex.build_mipmaps(); self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)

    def _build(self, chars, png, meta):
        f = _font(self.key)
        asc, desc = f.getmetrics()
        cols = 4096 // CELL; rows = (len(chars) + cols - 1) // cols
        H = rows * CELL; atlas = np.zeros((H, cols * CELL), np.uint8)
        glyphs = {}
        for i, ch in enumerate(chars):
            im = Image.new('L', (CELL * 2, CELL * 2), 0); d = ImageDraw.Draw(im)
            # baseline placed so the em box (asc+desc) is vertically centred in the cell
            ox = P * 2; oy = (CELL * 2 - (asc + desc) * 2) // 2
            big = ImageFont.truetype(FONTS[self.key][0], S * 2)
            if FONTS[self.key][1] is not None:
                try: big.set_variation_by_axes([FONTS[self.key][1]])
                except Exception: pass
            d.text((ox, oy), ch, font=big, fill=255)
            m = np.asarray(im).astype(np.float32) / 255.
            inside = m > .5
            dist = distance_transform_edt(~inside) - distance_transform_edt(inside)
            sdf = np.clip(.5 - dist / (SPREAD * 2) * .5, 0, 1)
            sdf = Image.fromarray((sdf * 255).astype(np.uint8)).resize((CELL, CELL), Image.LANCZOS)
            r, c = divmod(i, cols)
            atlas[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = np.asarray(sdf)
            glyphs[ch] = dict(i=i, adv=f.getlength(ch) / S)
        Image.fromarray(atlas).save(png)
        json.dump(dict(glyphs=glyphs, cols=cols, size=[cols * CELL, H], ascent=asc / S, descent=desc / S),
                  open(meta, 'w', encoding='utf-8'), ensure_ascii=False)

    def uv(self, ch):
        g = self.glyphs[ch]; r, c = divmod(g['i'], self.cols)
        W, H = self.size
        return (c * CELL / W, r * CELL / H, (c + 1) * CELL / W, (r + 1) * CELL / H)

    def adv(self, ch):
        return self.glyphs[ch]['adv'] if ch in self.glyphs else .35


# instance layout for text.vert
TEXT_LAYOUT = [('iPos', 2), ('iSize', 1), ('iRot', 1), ('iUV', 4), ('iFill', 4), ('iFill2', 4), ('iLine', 4), ('iParam', 4)]


class TextBatch:
    """Collect glyph instances; size = em size in px. Positions are glyph centres (em box centre)."""
    def __init__(self):
        self.rows = []

    def glyph(self, atlas, ch, x, y, size, rot=0., fill=(1, 1, 1, 1), fill2=None, line=(0, 0, 0, 1),
              outline=.12, glow=0., sweep=0., soft=0., alpha=1.):
        if ch not in atlas.glyphs: return
        cell = size * CELL / S
        f = tuple(fill[:3]) + (fill[3] * alpha,)
        f2 = tuple((fill2 or fill)[:3]) + ((fill2 or fill)[3] * alpha,)
        ln = tuple(line[:3]) + (line[3] * alpha,)
        # em box centre -> cell centre offset (glyph drawn starting at x=P in cell)
        adv = atlas.adv(ch)
        cx = x + (CELL / 2 - P - adv * S / 2) / S * size
        self.rows.append([cx, y, cell, rot, *atlas.uv(ch), *f, *f2, *ln, outline, glow, sweep, soft])

    def data(self):
        return np.array(self.rows, 'f4') if self.rows else np.zeros((0, 28), 'f4')


def layout(atlas, text, size, tracking=0.0):
    """x offsets (glyph centres) for a run of text, relative to run start; returns (centres, total width)."""
    xs = []; x = 0.0
    for ch in text:
        a = atlas.adv(ch) * size
        xs.append(x + a / 2); x += a + tracking * size
    return xs, x - tracking * size
