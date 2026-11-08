"""Live2D characters (Wonderlands×Showtime unit outfits + Miku) with a procedural performance layer."""
import os, glob, math
import numpy as np
import live2d
from OpenGL import GL
from .l2dmotion import Motion
from .motion3 import Motion3

# project root derived from this file, so the whole tree can be moved or copied without editing paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/')

L2D_ROOT = f'{ROOT}/assets_raw/活动3_资源与剧情包/04_WS_Live2D模型'
MIKU_ROOT = f'{ROOT}/assets_miku'
MIKU_MODEL = f'{MIKU_ROOT}/models/v2/main/21_miku/v2_21miku_wonder/21miku_wondershow2_t05.model3.json'
# cat tail split into its own model so it can sit behind other characters while the hair stays in front
MIKU_BODY = f'{ROOT}/assets_miku_split/notail/21miku_wondershow2_t05.model3.json'
MIKU_TAIL = f'{ROOT}/assets_miku_split/tailonly/21miku_wondershow2_t05.model3.json'
MIKU_MOTIONS = f'{MIKU_ROOT}/motions/v2/main/21_miku/v2_21miku_motion_base/motion'

MODELS = {'tsukasa': ('dir', '天马司/v2_13tsukasa_unit'), 'emu': ('dir', '凤笑梦/v2_14emu_unit'),
          'nene': ('dir', '草薙宁宁/v2_15nene_unit'), 'rui': ('dir', '神代类/v2_16rui_unit'),
          'miku': ('file', MIKU_BODY), 'miku_tail': ('file', MIKU_TAIL)}
MOTION_SRC = {'tsukasa': '天马司', 'rui': '天马司', 'emu': '凤笑梦', 'nene': '凤笑梦'}
EXTRA_SRC = {'rui': ['神代类'], 'nene': ['草薙宁宁'], 'tsukasa': [], 'emu': ['草薙宁宁']}
BASE_MOTION = {'tsukasa': 'm-proud07-pose', 'rui': 'm-adult09-pose', 'emu': 'w-adult02-pose',
               'nene': 'w-adult01-pose', 'miku': 'w-cool02-pose', 'miku_tail': 'w-cool02-pose'}
# the Miku sheet is drawn smaller inside its canvas than the WxS models: enlarge it a bit on screen
FIT = {'tsukasa': 1.0, 'rui': 1.0, 'emu': 1.0, 'nene': 1.0, 'miku': 1.0}

_inited = False


class Character:
    def __init__(self, eng, name, tex_w=1024, tex_h=2100):
        global _inited
        if not _inited:
            live2d.init(); live2d.glInit(); _inited = True
        self.e = eng; self.name = name
        kind, ref = MODELS[name]
        mj = glob.glob(os.path.join(L2D_ROOT, ref, '*.model3.json'))[0] if kind == 'dir' else ref
        self.m = live2d.Model(); self.m.LoadModelJson(mj)
        self.W, self.H = tex_w, tex_h
        self.m.Resize(tex_w, tex_h)
        self.ids = set(self.m.GetParamIds())
        self.motions = {}
        if name in ('miku', 'miku_tail'):
            for f in glob.glob(os.path.join(MIKU_MOTIONS, '*.motion3.json')):
                self.motions[os.path.basename(f).replace('.motion3.json', '')] = Motion3(f)
        else:
            for src in [MOTION_SRC[name]] + EXTRA_SRC[name]:
                for f in glob.glob(os.path.join(L2D_ROOT, src, '*', 'motion*', '*.anim')):
                    k = os.path.basename(f)[:-5]
                    if k not in self.motions:
                        try: self.motions[k] = Motion(f, list(self.ids))
                        except Exception: pass
        self.fbo, self.tex = eng.target(f'l2d_{name}', tex_w, tex_h, dtype='f1')
        self.rng = np.random.RandomState(abs(hash(name)) % 1000)
        self.blink_t = self.rng.uniform(0, 3)
        self.zoom = 1.0; self.off = (0.0, 0.0); self.fit = FIT.get(name, 1.0)

    def set(self, pid, v, w=1.0):
        if pid in self.ids: self.m.SetParamById(pid, float(v), w)

    def pose(self, t, dt, motion=None, mphase=None, mouth=0.0, beat_ph=0.0, energy=0.5, look=(0, 0),
             head=(0, 0, 0), body=(0, 0, 0), smile=0.0, eyes=1.0, cheek=0.0, sweat=0.0, zoom=None, off=None, bounce=0.0):
        m = self.m
        z = self.zoom if zoom is None else zoom
        if z != self.zoom: m.SetScale(z); self.zoom = z
        if off is not None and tuple(off) != self.off: m.SetOffset(*off); self.off = tuple(off)
        m.Update(dt)
        mo = self.motions.get(motion or BASE_MOTION[self.name])
        if mo is not None:
            ph = mo.duration if mphase is None else min(mphase, mo.duration)
            for p, v in mo.sample(ph).items():
                if p in self.ids and not p.startswith('ParamMouth'): m.SetParamById(p, v)
        # procedural performance layer
        b = math.sin(beat_ph * 2 * math.pi)
        bob = 0.5 - 0.5 * math.cos(beat_ph * 2 * math.pi)
        ph0 = (abs(hash(self.name)) % 100) / 100 * 6.28
        self.set('ParamAngleX', head[0] + 6 * energy * math.sin(t * 1.3 + ph0))
        self.set('ParamAngleY', head[1] + 14 * energy * (bob - .5) - 4 * bounce)
        self.set('ParamAngleZ', head[2] + 5 * energy * b)
        self.set('ParamBodyAngleX', body[0] + 4 * energy * math.sin(t * 0.9 + 1))
        self.set('ParamBodyAngleY', body[1] + 6 * energy * bob)
        self.set('ParamBodyAngleZ', body[2] + 4 * energy * b)
        self.set('ParamEyeballX', look[0]); self.set('ParamEyeballY', look[1])
        # blink
        self.blink_t -= dt
        bl = 1.0
        if self.blink_t < 0.12:
            bl = abs(self.blink_t - 0.06) / 0.06
            if self.blink_t < 0: self.blink_t = 2.5 + self.rng.uniform(0, 2.5)
        eyes = min(max(eyes, 0.), min(1., bl))
        self.set('ParamEyeLOpen', eyes); self.set('ParamEyeROpen', eyes)
        self.set('ParamEyeLSmile', smile); self.set('ParamEyeRSmile', smile)
        self.set('ParamMouthOpenY', mouth)
        self.set('ParamMouthForm', 0.3 + 0.7 * smile)
        self.set('ParamCheek', cheek)
        self.set('ParamSweatOn', sweat)
        self.set('ParamBreath', 0.5 + 0.5 * math.sin(t * 2.2))

    def render(self):
        self.fbo.use(); self.e.ctx.clear(0, 0, 0, 0)
        # Cubism's GL renderer expects a clean binding state (client-side arrays, no VAO/VBO bound)
        GL.glBindVertexArray(0); GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0); GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glUseProgram(0); GL.glActiveTexture(GL.GL_TEXTURE0)
        self.m.Draw()
        GL.glBindVertexArray(0); GL.glUseProgram(0)
        return self.tex
