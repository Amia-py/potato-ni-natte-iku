"""The potatoになっていく MV director: assets, shot list, per-frame composition."""
import os, glob, math
import numpy as np
import moderngl
from engine.gl import Engine
from engine.draw import Draw, Instanced
from engine.text import Atlas, TextBatch, TEXT_LAYOUT, layout
from engine.l2d import Character
from engine import lineart
from .common import *
from .lyrics import Lyrics, MEMBER
from . import typo

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/')
ASSET = f'{ROOT}/assets_raw/活动3_资源与剧情包'
EV = f'{ASSET}/00_重点_活动3剧情卡面'
CARDS = {
    'rui_a': '119_神代类_★4_意想不到的肺腑之言_觉醒前', 'rui_b': '119_神代类_★4_意想不到的肺腑之言_觉醒后',
    'tsu_a': '120_天马司_★4_担惊受怕？！落荒而逃！_觉醒前', 'tsu_b': '120_天马司_★4_担惊受怕？！落荒而逃！_觉醒后',
    'emu_a': '122_凤笑梦_★3_骑上熊猫_觉醒前', 'emu_b': '122_凤笑梦_★3_骑上熊猫_觉醒后',
    'nen_a': '123_草薙宁宁_★2_奇幻手杖_觉醒前',
}
SPRITE_CH = {'tsukasa': '天马司', 'emu': '凤笑梦', 'nene': '草薙宁宁', 'rui': '神代类'}
NAMES = {'tsukasa': ('天馬司', 'TSUKASA TENMA'), 'emu': ('鳳えむ', 'OTORI EMU'),
         'nene': ('草薙寧々', 'KUSANAGI NENE'), 'rui': ('神代類', 'KAMISHIRO RUI'),
         'miku': ('初音ミク', 'HATSUNE MIKU')}
# Rui's song, so he leads; Miku is the fifth SEKAI singer
ORDER = ['rui', 'tsukasa', 'emu', 'nene', 'miku']
ROSTER = ORDER
BASE_MOTION = {'tsukasa': 'm-proud07-pose', 'rui': 'm-adult09-pose', 'emu': 'w-adult02-pose',
               'nene': 'w-adult01-pose', 'miku': 'w-cool02-pose', 'miku_tail': 'w-cool02-pose'}
MIKU_IMG = 'D:/Downloads/miku_ws_normal.png'

EXTRA_TEXT = ('Wonderlands×Showtime presents HALLOWEEN SHOW potatoになっていく Neru 作詞・作曲・編曲 歌 ワンダーランズ×ショウタイム '
              '初音ミク 天馬司鳳えむ草薙寧々神代類 TSUKASA TENMA EMU OTORI NENE KUSANAGI RUI KAMISHIRO HATSUNE MIKU '
              '0123456789 ！？♪★… .,:;/|-–—_()[]{}<>+=*&%#@\'"~ ¥·※'
              'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
# every glyph the showbill typesets must be here, or SDF atlas drops it silently
EXTRA_TEXT += ('あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
               'がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゃゅょっぁぃぅぇぉ'
               'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'
               'ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポャュョッァィゥェォヴ'
               '、。・ー〜「」『』（）〈〉《》【】〔〕！？…‥：；')
EXTRA_TEXT += ('開演奏終演完幕第本日目出演者印刷編集発行定価奥付検印転換中暗青春涙笑抗弁勲章行進数字煮頃'
               '火事場油善悪掛違違身振払下方抗生活計画全部将来像成功法泡吹白目茹上散溶未来暮'
               '時間無我等見下権利有象無象発増減退屈破裂壊捨拾得損得得損'
               '舞台袖奈落喝采大成功変身土豆芋一覧技稽古初千秋楽切符入場整理番号指定席自由前売当日券大小人円税込枚組内容量原材料名賞味期限保存方法製造販売'
               '観客動員総勢様御来場誠圧倒的感謝致裏方照明音響美術衣装監督補佐助手見習研修生'
               '嘘本当正解不正的中外秒分経過残少押閉上下左右周辺中央章活炭酸抜粋核骨肉厚薄濃淡色形')

POST_DEFAULT = dict(uBloomAmt=.7, uCA=.6, uGrain=.035, uVignette=.55, uFlash=(1., 1., 1., 0.), uCrumple=0., uBallScale=1.,
                    uBallRot=0., uBallOff=(0., 0.), uBg=(.06, .03, .1), uHalftone=0., uSat=1.08, uContrast=1.04,
                    uTint=(1., 1., 1.), uLetterbox=0., uShake=(0., 0.), uMono=0., uRetro=.5,
                    uLift=0., uLiftCol=(.07, .055, .04), uBloomTint=(1., 1., 1.))


class MV:
    def __init__(self, W=1920, H=1080):
        self.W, self.H = W, H
        self.e = Engine(W, H); self.d = Draw(self.e); self.ctx = self.e.ctx
        self.au = Audio()
        self.at = None
        self.lyr = None
        # targets
        self.scene_fbo, self.scene_tex = self.e.target('scene')
        self.a_fbo, self.a_tex = self.e.target('shotA')
        self.b_fbo, self.b_tex = self.e.target('shotB')
        self.tv_fbo, self.tv_tex = self.e.target('tvscreen', 960, 720)
        self.bl1, self.bt1 = self.e.target('bl1', W // 4, H // 4)
        self.bl2, self.bt2 = self.e.target('bl2', W // 4, H // 4)
        self.out_fbo, self.out_tex = self.e.target('out', dtype='f1')
        self.cur = self.scene_fbo
        # text
        lyr_chars = None
        self.lyr = Lyrics.__new__(Lyrics)
        tmp = Lyrics.__new__(Lyrics); tmp.lines = __import__('json').load(open(f'{WORK}/lyrics_timing.json', encoding='utf-8'))
        chars = set(EXTRA_TEXT)
        for L in tmp.lines:
            for c in L['chars']:
                chars |= set(c['t']); chars |= set(c['ruby'] or '')
        self.at = Atlas(self.e, 'jp_black', chars, f'{WORK}/cache')
        self.at_serif = Atlas(self.e, 'serif_black', chars, f'{WORK}/cache')
        # showbill faces
        self.f_serif = Atlas(self.e, 'serif', chars, f'{WORK}/cache')
        self.f_pop = Atlas(self.e, 'pop', chars, f'{WORK}/cache')
        self.f_round = Atlas(self.e, 'round', chars, f'{WORK}/cache')
        self.f_dot = Atlas(self.e, 'dot', chars, f'{WORK}/cache')
        self.f_decol = Atlas(self.e, 'decol', chars, f'{WORK}/cache')
        self.f_mono = Atlas(self.e, 'mono', chars, f'{WORK}/cache')
        self.lyr = Lyrics(self.at)
        self.txt = Instanced(self.e, 'text.frag', 'text.vert', TEXT_LAYOUT, maxn=3000)
        self.parts_r = Instanced(self.e, 'particles.frag', 'particles.vert', PART_LAYOUT, maxn=3000)
        # images
        self.card = {k: self.e.texture(f'{EV}/01_卡面_全分辨率/{v}.png', max_size=2340) for k, v in CARDS.items()}
        self.crop = {k: self.e.texture(f'{EV}/03_卡面裁切_透明/{v}.png') for k, v in CARDS.items()}
        self.card['miku'] = self.e.texture(MIKU_IMG, max_size=2520)
        self.spr = {}
        for k, cn in SPRITE_CH.items():
            fs = sorted(glob.glob(f'{ASSET}/03_WS_剧情立绘/{cn}_*.png'))
            self.spr[k] = fs
        self._spr_cache = {}
        self._ln = {}
        self._chln = {}
        self._pose_k = 0
        self._poses = {}
        self._pi = {}
        self._pose_cache = {}
        self._shot_id = 0
        allcrops = sorted(glob.glob(f'{ASSET}/02_WS_卡面裁切_全部/*.png'))
        self.allcrops = allcrops
        # characters
        self.ch = {k: Character(self.e, k) for k in ROSTER + ['miku_tail']}
        self.l2d_time = {}
        self.dt = 1 / 60
        self.tail_split = False
        self.shots = self.build_shots()

    # ------------------------------------------------------------ assets
    # ------------------------------------------------------------ line-art plates
    def ln(self, path, **kw):
        key = (path, tuple(sorted(kw.items())))
        if key not in self._ln:
            self._ln[key] = lineart.load(self.e, path, **kw)
        return self._ln[key]

    def card_ln(self, k):
        p = MIKU_IMG if k == 'miku' else f'{EV}/01_卡面_全分辨率/{CARDS[k]}.png'
        return self.ln(p, lo=.20, hi=.46, thick=3, min_frac=.035, focus=1.4)

    def crop_ln(self, k):
        return self.ln(f'{EV}/03_卡面裁切_透明/{CARDS[k]}.png', lo=.13, hi=.31, thick=3)

    def pose_files(self, who):
        """every drawn sheet for this character, in order"""
        import glob as _g
        if who not in self._poses:
            fs = sorted(_g.glob(f'{ROOT}/work/lineart_src/{who}_*.png'))
            if not fs:
                fs = [f'{ROOT}/work/lineart_src/{who}.png']
            self._poses[who] = fs
        return self._poses[who]

    def gen_ln(self, who, k=None):
        """hand-drawn pose library; the index walks the list so every sheet gets used"""
        fs = self.pose_files(who)
        path = fs[(k or 0) % len(fs)]
        key = ('gen', path)
        if key not in self._chln:
            self._chln[key] = lineart.from_ink(self.e, path, os.path.basename(path).rsplit('.', 1)[0])
        if os.environ.get('POSE_LOG'):
            with open(f'{ROOT}/work/pose_used.txt', 'a', encoding='utf-8') as f:
                f.write(os.path.basename(path) + "\n")
        return self._chln[key]

    def intro_ln(self, who):
        """the single portrait used on the cast pages"""
        path = f'{ROOT}/work/lineart_src/{who}.png'
        key = ('intro', path)
        if key not in self._chln:
            self._chln[key] = lineart.from_ink(self.e, path, who + '_intro')
        return self._chln[key]

    def spr_ln(self, who, i):
        return self.ln(self.spr[who][i % len(self.spr[who])], lo=.09, hi=.30, thick=2)

    def char_ln(self, who, motion=None, mphase=.5):
        """full-body line drawing: render the model once, trace it, cache the result.
        The model is only a source of shapes here — nothing is rigged or animated."""
        key = (who, motion, round(mphase, 3))
        if key in self._chln:
            return self._chln[key]
        c = self.ch[who]
        c.pose(0.6, 1 / 60, motion=motion, mphase=mphase, energy=.30, beat_ph=0.,
               mouth=0., smile=.30, eyes=1.)
        c.render()
        self.cur.use()
        from PIL import Image
        img = Image.fromarray(self.e.read(c.fbo))
        tag = 'c_%s_%s_%03d' % (who, (motion or 'base').replace('-', ''), int(mphase * 100))
        t = lineart.from_image(self.e, img, tag, lo=.115, hi=.335, thick=2, soft=.50, work=1100)
        self._chln[key] = t
        return t

    def sprite_tex(self, who, i):
        fs = self.spr[who]; f = fs[i % len(fs)]
        if f not in self._spr_cache: self._spr_cache[f] = self.e.texture(f)
        return self._spr_cache[f]

    def cropall_tex(self, i):
        f = self.allcrops[i % len(self.allcrops)]
        if f not in self._spr_cache: self._spr_cache[f] = self.e.texture(f)
        return self._spr_cache[f]

    # ------------------------------------------------------------ drawing primitives
    def bg(self, frag, blend=False, **u):
        self.e.pass_(frag, self.cur, blend=blend, uTime=self.t, **u)

    def stage(self, **u):
        d = dict(uCurtain=1., uWall=(.3, .1, .45), uCurtainCol=(.55, .04, .1), uSpot=[0] * 16, uSpotCol=[1] * 12,
                 uBulbs=1., uChase=self.au.beats(self.t), uGrave=0., uMoon=0., uBeat=self.au.beat_pulse(self.t), uHaze=1., uDeco=0.)
        d.update(u); self.bg('stage.frag', **d)

    def stew(self, **u):
        d = dict(uColA=(.35, .08, .02), uColB=(.95, .45, .12), uColC=(1., .85, .5), uSwirl=1., uBubble=.7,
                 uBeat=self.au.pulse(self.t, 'kick'), uHeat=.4, uFlow=0., uZoom=1., uCenter=(.5, .5))
        d.update(u); self.bg('stew.frag', **d)

    def comic(self, **u):
        d = dict(uColA=(.1, .05, .2), uColB=(.3, .1, .4), uMode=0., uFocus=(.5, .5), uBeat=self.au.beat_pulse(self.t), uSpin=.2)
        d.update(u); self.bg('comic.frag', **d)

    # ------------------------------------------------------------ showbill primitives
    def paper(self, **u):
        """the printed page; uMode=1 for the inverted ink page"""
        d = dict(uPaper=typo.PAPER, uInk=typo.INK, uAccent=typo.PURPLE, uMode=0., uRules=1., uFrame=1.,
                 uGrain=.05, uVignette=.30, uBeat=self.au.pulse(self.t, 'kick'), uHalftone=0., uGlow=1., uFilm=1., uGrid=0.)
        d.update(u); self.bg('paper.frag', **d)

    def rect(self, x, y, w, h, color=(0, 0, 0), alpha=1., rot=0.):
        """flat block of ink / spot colour, top-left anchored"""
        if getattr(self, '_white', None) is None:
            self._white = self.ctx.texture((1, 1), 4, bytes([255, 255, 255, 255]))
        self.img(self._white, x + w / 2, y + h / 2, w, h, rot, uOpacity=alpha, uTint=(*color, 1.))

    def potato(self, x, y, r, rot=0., seed=0., face=0., squash=0., blink=0., fill=None, alpha=1.,
               offset=.02, accent=None):
        """one flat line-art potato"""
        self.e.pass_('potato_ink.frag', self.cur, blend=True, uTime=self.t, uCenter=(x, y), uRadius=r,
                     uRot=rot, uSeed=float(seed), uFace=float(face), uSquash=squash, uBlink=blink, uAlpha=alpha,
                     uFill=fill or (.976, .906, .741), uInk=typo.INK, uAccent=accent or typo.YELLOW, uOffset=offset)

    def potatoes(self, pots, rim=(1., .5, .8), key=(-.5, .8, .6), exposure=1., glow=0., squash=0.):
        if not pots: return
        u = potato_uniforms(pots, glow, squash)
        self.e.pass_('potatoes.frag', self.cur, blend=True, uTime=self.t, uRim=rim, uKeyDir=key, uExposure=exposure, **u)

    def fire(self, height=.4, intensity=1., inner=(1., .85, .3), outer=(1., .3, .05)):
        self.e.pass_('fire.frag', self.cur, blend=True, uTime=self.t, uHeight=height, uIntensity=intensity,
                     uBeat=self.au.pulse(self.t, 'kick'), uInner=inner, uOuter=outer)

    def img(self, tex, cx, cy, w, h, rot=0., uv=(0, 0, 1, 1), **fx):
        self.d.time = self.t
        self.d.sprite(tex, (cx, cy), (w, h), rot, uv, target=self.cur, **fx)

    def cover(self, tex, zoom=1.0, pan=(0., 0.), rot=0., **fx):
        w, h = self.d.fit(tex, self.W, self.H)
        w *= zoom; h *= zoom
        self.img(tex, self.W / 2 + pan[0] * (w - self.W) / 2, self.H / 2 + pan[1] * (h - self.H) / 2, w, h, rot, **fx)

    def l2d(self, who, x, y, height, motion=None, mphase=None, rot=0., sing=True, **pose_fx):
        """draw a live2d character; (x, y) = centre of the texture in px; height = on-screen texture height"""
        if who == 'miku' and not self.tail_split:
            self.l2d('miku_tail', x, y, height, motion, mphase, rot, sing, **pose_fx)
        fx = {k: v for k, v in pose_fx.items() if k.startswith('u')}
        pose = {k: v for k, v in pose_fx.items() if not k.startswith('u')}
        c = self.ch[who]
        t = self.t
        mouth = 0.0
        if sing and self.lyr.active(t, pre=.05, post=.05):
            mouth = clamp(self.au('rms_vocal', t) * 1.5 - .1)
        pose.setdefault('mouth', mouth)
        pose.setdefault('beat_ph', self.au.beat_phase(t))
        pose.setdefault('energy', .3 + .7 * self.au('rms', t, 6))
        c.pose(t, self.dt, motion=motion or BASE_MOTION[who], mphase=mphase, **pose)
        tex = c.render()
        self.cur.use()
        w = height * c.W / c.H
        self.img(tex, x, y, w, height, rot, **fx)

    def cast(self):
        """(slot, name) for one row of the cast: Miku's tail first so it sits behind everybody, her body last"""
        self.tail_split = True
        try:
            yield ROSTER.index('miku'), 'miku_tail'
            for j, who in enumerate(ROSTER): yield j, who
        finally:
            self.tail_split = False

    def parts(self, rows, additive=False):
        if rows: self.parts_r.render(np.array(rows, 'f4'), target=self.cur, additive=additive)

    def text(self, s, x, y, size, font=None, fill=(1, 1, 1), fill2=None, line=(.08, .03, .12, 1), outline=.16, glow=0.,
             align='center', rot=0., alpha=1., tracking=0., tb=None, sweep=0.):
        at = font or self.at
        xs, w = layout(at, s, size, tracking)
        x0 = x - w / 2 if align == 'center' else (x if align == 'left' else x - w)
        own = tb is None
        tb = tb or TextBatch()
        c, sn = math.cos(rot), math.sin(rot)
        for ch, gx in zip(s, xs):
            dx = x0 + gx - x
            tb.glyph(at, ch, x + dx * c, y + dx * sn, size, rot, fill=(*fill, 1), fill2=(*(fill2 or fill), 1), line=line,
                     outline=outline, glow=glow, alpha=alpha, sweep=sweep)
        if own: self.flush(tb, at)
        return w

    def flush(self, tb, at=None):
        self.txt.render(tb.data(), {'uAtlas': (at or self.at).tex}, target=self.cur)

    def lyrics(self, t, exclusive=None, **kw):
        tb = TextBatch()
        act = self.lyr.active(t, pre=.4, post=1.2)
        if exclusive is None: exclusive = kw.get('style') == 'tv' or kw.get('vertical', False)
        if exclusive and act:
            started = [L for L in act if t >= L['start'] - .05]
            act = started[-1:] if started else act[:1]
        for L in act:
            st = kw.get('style_fn', lambda L: {})(L)
            args = dict(kw); args.pop('style_fn', None); args.update(st)
            self.lyr.draw_line(tb, L, t, **args)
        self.flush(tb)

    # ------------------------------------------------------------ frame
    def frame(self, t):
        self.t = t
        shot, nxt = None, None
        for i, s in enumerate(self.shots):
            if s['t0'] <= t < s['t1']: shot = s; break
        if shot is None: shot = self.shots[-1]
        post = dict(POST_DEFAULT)
        tr = shot.get('trans')
        if tr and t < shot['t0'] + tr[1] and i > 0:
            prev = self.shots[i - 1]
            self.cur = self.a_fbo; self.ctx.clear(0, 0, 0, 1) if False else None
            self.a_fbo.use(); self.ctx.clear(0, 0, 0, 1)
            p1 = prev['fn'](t, t - prev['t0'], prev['t1'] - prev['t0']) or {}
            self.cur = self.b_fbo; self.b_fbo.use(); self.ctx.clear(0, 0, 0, 1)
            p2 = shot['fn'](t, t - shot['t0'], shot['t1'] - shot['t0']) or {}
            k = clamp((t - shot['t0']) / tr[1])
            self.e.pass_('wipe.frag', self.scene_fbo, {'uA': self.a_tex, 'uB': self.b_tex}, uProg=ease_inout(k) if tr[0] != 2 else k,
                         uMode=float(tr[0]), uFocus=tr[2] if len(tr) > 2 else (.5, .5), uTime=t)
            post.update(p1 if k < .5 else p2)
        else:
            self.cur = self.scene_fbo; self.scene_fbo.use(); self.ctx.clear(0, 0, 0, 1)
            post.update(shot['fn'](t, t - shot['t0'], shot['t1'] - shot['t0']) or {})
        # bloom + post
        self.e.pass_('blur.frag', self.bl1, {'uSrc': self.scene_tex}, uDir=(1., 0.), uThresh=.75)
        self.e.pass_('blur.frag', self.bl2, {'uSrc': self.bt1}, uDir=(0., 1.), uThresh=-1.)
        self.e.pass_('blur.frag', self.bl1, {'uSrc': self.bt2}, uDir=(1.5, 0.), uThresh=-1.)
        self.e.pass_('blur.frag', self.bl2, {'uSrc': self.bt1}, uDir=(0., 1.5), uThresh=-1.)
        post['uTime'] = t
        self.e.pass_('post.frag', self.out_fbo, {'uScene': self.scene_tex, 'uBloom': self.bt2}, **post)
        return self.out_fbo

    from .shots_new import build_shots
