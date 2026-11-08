"""Turn a transparent character render into a clean line drawing.

Only the figure survives: the source alpha is the matte, so no background edges can leak
in. The image is first cropped to the figure and scaled to a fixed working size, which
makes the stroke weight identical across every character regardless of the original
resolution — that is what keeps the line language consistent through the cut.
"""
import os, json, hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel, maximum_filter, label, binary_opening, binary_dilation

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/')
CACHE = f'{ROOT}/work/lineart'

WORK = 1100          # longest side of the working image, so 1 px of stroke stays 1 px


def _key(path, params):
    h = hashlib.md5((path + json.dumps(params, sort_keys=True)).encode('utf-8')).hexdigest()[:16]
    return os.path.join(CACHE, os.path.basename(path).split('.')[0][:22] + '_' + h + '.png')


def crop_to_alpha(im, pad=6):
    a = np.asarray(im.convert('RGBA'))[..., 3]
    ys, xs = np.where(a > 8)
    if len(ys) == 0:
        return im.convert('RGBA')
    y0, y1 = max(0, ys.min() - pad), min(im.height, ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(im.width, xs.max() + pad)
    return im.convert('RGBA').crop((x0, y0, x1, y1))


def _salient(e, min_frac=.006):
    """keep only the长 connected line networks — background specks and dots fall away"""
    b = binary_opening(e > .22, np.ones((2, 2)))
    lab, n = label(b, np.ones((3, 3)))
    if n == 0:
        return e
    sizes = np.bincount(lab.ravel())
    floor = max(80., sizes[1:].max() * min_frac)
    keep = np.zeros_like(b)
    for i in range(1, n + 1):
        if sizes[i] >= floor:
            keep |= (lab == i)
    keep = binary_dilation(keep, np.ones((3, 3)))
    return e * keep


def line_art(im, ink=(.098, .080, .062), lo=.085, hi=.300, gain=2.2, thick=2, soft=.50,
             work=WORK, ink_alpha=.94, keep_alpha=True, do_crop=True, min_frac=.0, focus=.0):
    im = im.convert('RGBA')
    if do_crop:
        im = crop_to_alpha(im)
    # normalise the working resolution -> uniform stroke weight on screen
    sc = work / max(im.size)
    if abs(sc - 1.) > .01:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    a0 = np.asarray(im, np.float32) / 255.
    g = a0[..., 0] * .299 + a0[..., 1] * .587 + a0[..., 2] * .114
    s = gaussian_filter(g, 1.9)                        # drop fabric folds and fine texture
    mag = np.hypot(sobel(s, 0), sobel(s, 1))
    m = mag / max(mag.max(), 1e-6)
    e = np.clip((m - lo) / max(hi - lo, 1e-6), 0., 1.) ** (1. / gain)
    e = maximum_filter(e, thick) * .85 + e * .15
    if min_frac > 0.:                                  # drop everything not part of a figure
        e = _salient(e, min_frac)
    if focus > 0.:                                     # fade the frame edges, keep the centre
        hh, ww = e.shape
        yy = np.linspace(-1, 1, hh)[:, None]; xx = np.linspace(-1, 1, ww)[None, :]
        r = np.sqrt((xx * 1.02) ** 2 + (yy * .92) ** 2)
        e = e * np.clip((1.06 - r) / .30, 0., 1.) ** focus
    e = gaussian_filter(e, soft)                       # soft drawn edge, not a hard cut
    if keep_alpha:
        e = e * np.clip(a0[..., 3] * 1.15, 0., 1.)     # the sprite alpha is the matte
    rgb = np.empty(e.shape + (3,), np.float32)
    rgb[...] = ink
    out = np.dstack([rgb, e * ink_alpha])
    return Image.fromarray((out * 255).astype(np.uint8), 'RGBA')


def load(eng, path, **params):
    os.makedirs(CACHE, exist_ok=True)
    k = _key(path, params)
    if not os.path.exists(k):
        line_art(Image.open(path), **params).save(k)
    return eng.texture(k)


def from_image(eng, im, tag, **params):
    """line-art an in-memory PIL image, cached on disk under `tag`"""
    os.makedirs(CACHE, exist_ok=True)
    k = os.path.join(CACHE, 'r_' + tag + '.png')
    if not os.path.exists(k):
        line_art(im, **params).save(k)
    return eng.texture(k)


def from_ink(eng, path, tag, ink=(.098, .080, .062), work=WORK, ink_alpha=.94, bust=0.):
    """take an already-drawn line drawing on white and turn it into ink on transparency"""
    os.makedirs(CACHE, exist_ok=True)
    k = os.path.join(CACHE, 'ink_' + tag + '.png')
    if not os.path.exists(k):
        im = Image.open(path).convert('RGB')
        a = np.asarray(im, np.float32) / 255.
        l = a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
        al = gaussian_filter(np.clip((.93 - l) / .55, 0., 1.), .5)
        rgb = np.empty(al.shape + (3,), np.float32)
        rgb[...] = ink
        out = Image.fromarray((np.dstack([rgb, al * ink_alpha]) * 255).astype(np.uint8), 'RGBA')
        out = crop_to_alpha(out, pad=10)
        if bust > 0.:
            out = out.crop((0, 0, out.width, max(1, int(out.height * bust))))
        sc = work / max(out.size)
        if abs(sc - 1.) > .01:
            out = out.resize((max(1, int(out.width * sc)), max(1, int(out.height * sc))), Image.LANCZOS)
        out.save(k)
    return eng.texture(k)
