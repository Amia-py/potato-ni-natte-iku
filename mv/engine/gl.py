"""Minimal offscreen GL engine: moderngl on a hidden glfw window (shared with live2d-py)."""
import os, re
import numpy as np
import glfw, moderngl
from PIL import Image

SHADER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shaders')

FS_VERT = """#version 330
in vec2 in_pos;
out vec2 uv;
void main() { uv = in_pos * 0.5 + 0.5; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

def load_glsl(name, seen=None):
    seen = seen if seen is not None else set()
    src = open(os.path.join(SHADER_DIR, name), encoding='utf-8').read()
    def inc(m):
        f = m.group(1)
        if f in seen: return ''
        seen.add(f)
        return load_glsl(f, seen)
    return re.sub(r'^#include\s+"([^"]+)"', inc, src, flags=re.M)


class Engine:
    def __init__(self, W, H):
        self.W, self.H = W, H
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        self.win = glfw.create_window(64, 64, 'mv', None, None)
        glfw.make_context_current(self.win)
        self.ctx = moderngl.create_context()
        self.quad = self.ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], 'f4'))
        self.progs, self.vaos, self.targets, self.textures = {}, {}, {}, {}

    # ---------- programs ----------
    def prog(self, frag, vert=None):
        key = (frag, vert)
        if key not in self.progs:
            vs = load_glsl(vert) if vert else FS_VERT
            p = self.ctx.program(vertex_shader=vs, fragment_shader=load_glsl(frag))
            self.progs[key] = p
            if vert is None:
                self.vaos[key] = self.ctx.vertex_array(p, [(self.quad, '2f', 'in_pos')])
        return self.progs[key]

    def set(self, p, **u):
        for k, v in u.items():
            if k in p:
                if isinstance(v, moderngl.Texture):
                    continue
                un = p[k]
                if getattr(un, 'array_length', 1) > 1:
                    a = np.zeros(un.array_length * un.dimension, 'i4' if un.fmt.endswith('i') else 'f4')
                    flat = np.asarray(v, dtype=a.dtype).ravel()[:len(a)]
                    a[:len(flat)] = flat
                    un.write(a.tobytes())
                else:
                    un.value = v

    def bind_textures(self, p, tex):
        for i, (name, t) in enumerate(tex.items()):
            if name in p:
                t.use(i); p[name].value = i

    def pass_(self, frag, target, tex=None, blend=False, clear=None, **u):
        """full-screen pass into target (None = no fbo switch)"""
        p = self.prog(frag)
        if target is not None: target.use()
        if clear is not None: self.ctx.clear(*clear)
        self.reset_state(blend)
        self.bind_textures(p, tex or {})
        self.set(p, uResolution=(float(target.width if target else self.W), float(target.height if target else self.H)), **u)
        self.vaos[(frag, None)].render(moderngl.TRIANGLE_STRIP)

    def reset_state(self, blend=False, premul=True):
        ctx = self.ctx
        ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        if blend:
            ctx.enable(moderngl.BLEND)
            ctx.blend_func = (moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA) if premul else (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA, moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA)
            ctx.blend_equation = moderngl.FUNC_ADD
        else:
            ctx.disable(moderngl.BLEND)

    # ---------- targets / textures ----------
    def target(self, name, w=None, h=None, dtype='f2'):
        w = w or self.W; h = h or self.H
        key = (name, w, h, dtype)
        if key not in self.targets:
            t = self.ctx.texture((w, h), 4, dtype=dtype)
            t.filter = (moderngl.LINEAR, moderngl.LINEAR); t.repeat_x = t.repeat_y = False
            self.targets[key] = (self.ctx.framebuffer([t]), t)
        return self.targets[key]

    def texture(self, path_or_img, key=None, mip=True, premul=True, max_size=None):
        key = key or path_or_img
        if isinstance(key, str) and key in self.textures: return self.textures[key]
        im = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
        im = im.convert('RGBA')
        if max_size and max(im.size) > max_size:
            im.thumbnail((max_size, max_size), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255.0
        if premul: a[..., :3] *= a[..., 3:4]
        a = (a * 255 + 0.5).astype(np.uint8)[::-1].copy()
        t = self.ctx.texture(im.size, 4, a.tobytes())
        if mip:
            t.build_mipmaps(); t.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR); t.anisotropy = 8.0
        t.repeat_x = t.repeat_y = False
        if isinstance(key, str): self.textures[key] = t
        return t

    def read(self, fbo):
        return np.frombuffer(fbo.read(components=4, dtype='f1'), np.uint8).reshape(fbo.height, fbo.width, 4)[::-1]
