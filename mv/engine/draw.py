"""Draw helpers on top of Engine: sprites (one call each), instanced SDF text, instanced particles."""
import numpy as np, moderngl

SPRITE_DEFAULTS = dict(uOpacity=1.0, uTint=(1, 1, 1, 0), uAdd=(0, 0, 0), uOutline=0.0, uOutlineColor=(1, 1, 1),
                       uShadow=0.0, uDuo=0.0, uDuoA=(0, 0, 0), uDuoB=(1, 1, 1), uMelt=0.0, uHalftone=0.0,
                       uMask=0.0, uMaskRound=0.0, uDesat=0.0, uGlitch=0.0, uWobble=0.0, uSkew=(0, 0), uPad=0.0, uClip=(0.0, 0.0))


class Draw:
    def __init__(self, eng):
        self.e = eng; self.ctx = eng.ctx
        self.sp = eng.prog('sprite.frag', 'sprite.vert')
        self.sp_vao = self.ctx.vertex_array(self.sp, [(eng.quad, '2f', 'in_pos')])
        self.time = 0.0

    def sprite(self, tex, center, size, rot=0.0, uv=(0, 0, 1, 1), target=None, **fx):
        """center/size in px of `target` (default: currently bound fbo with engine resolution)."""
        u = dict(SPRITE_DEFAULTS); u.update(fx)
        if u['uOutline'] > 0 and u['uPad'] == 0: u['uPad'] = u['uOutline'] + 2
        if target is not None: target.use()
        res = (float(target.width), float(target.height)) if target is not None else (float(self.e.W), float(self.e.H))
        self.e.reset_state(blend=True)
        tex.use(0); self.sp['uTex'].value = 0
        self.e.set(self.sp, uResolution=res, uCenter=tuple(map(float, center)), uSize=tuple(map(float, size)),
                   uRot=float(rot), uUV=tuple(map(float, uv)), uTexSize=(float(tex.width), float(tex.height)),
                   uTime=self.time, **{k: (tuple(map(float, v)) if isinstance(v, (tuple, list)) else float(v)) for k, v in u.items()})
        self.sp_vao.render(moderngl.TRIANGLE_STRIP)

    def fit(self, tex, box_w, box_h, mode='cover'):
        """size of a texture fitted into a box"""
        a = tex.width / tex.height
        if (mode == 'cover') == (box_w / box_h > a):
            return box_w, box_w / a
        return box_h * a, box_h


class Instanced:
    """Generic instanced quad renderer. Instance layout given as list of (name, ncomp)."""
    def __init__(self, eng, frag, vert, layout, maxn=4096):
        self.e = eng; self.ctx = eng.ctx
        self.prog = eng.prog(frag, vert)
        self.layout = layout; self.stride = sum(n for _, n in layout)
        self.buf = self.ctx.buffer(reserve=maxn * self.stride * 4, dynamic=True)
        fmt = ' '.join(f'{n}f' for _, n in layout) + '/i'
        self.vao = self.ctx.vertex_array(self.prog, [(eng.quad, '2f', 'in_pos'), (self.buf, fmt, *[k for k, _ in layout])])
        self.maxn = maxn

    def render(self, data, textures=None, target=None, additive=False, **uniforms):
        n = len(data)
        if n == 0: return
        data = np.ascontiguousarray(data, dtype='f4')[:self.maxn]
        self.buf.write(data.tobytes())
        if target is not None: target.use()
        self.e.reset_state(blend=True)
        if additive: self.ctx.blend_func = (moderngl.ONE, moderngl.ONE)
        for i, (k, t) in enumerate((textures or {}).items()):
            t.use(i); self.prog[k].value = i
        res = (float(target.width), float(target.height)) if target is not None else (float(self.e.W), float(self.e.H))
        self.e.set(self.prog, uResolution=res, **uniforms)
        self.vao.render(moderngl.TRIANGLE_STRIP, instances=min(n, self.maxn))
