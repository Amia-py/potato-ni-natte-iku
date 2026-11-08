import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from engine.gl import Engine
from engine.draw import Draw, Instanced
from engine.text import Atlas, TextBatch, TEXT_LAYOUT, layout
from engine.l2d import Character
W, H = 1920, 1080
e = Engine(W, H); d = Draw(e)
fbo, tex = e.target('scene')
t0 = time.time()
at = Atlas(e, 'jp_black', 'ぜんぶがpotatoになっていく全部', 'D:/MV_DS/work/cache')
print('atlas', time.time() - t0)
txt = Instanced(e, 'text.frag', 'text.vert', TEXT_LAYOUT)
chars = {k: Character(e, k) for k in ['tsukasa', 'emu', 'nene', 'rui']}
card = e.texture('D:/MV_DS/assets_raw/活动3_资源与剧情包/00_重点_活动3剧情卡面/01_卡面_全分辨率/120_天马司_★4_担惊受怕？！落荒而逃！_觉醒后.png', max_size=2048)
fbo.use(); e.ctx.clear(0.1, 0.05, 0.15, 1)
d.sprite(card, (W/2, H/2), d.fit(card, W, H), uDesat=0.3)
for i, (k, c) in enumerate(chars.items()):
    c.pose(1.0, 1/30, motion={'tsukasa': 'm-proud07-pose', 'rui': 'm-adult09-pose', 'emu': 'w-adult02-pose', 'nene': 'w-adult01-pose'}[k], mouth=0.6, smile=0.5, energy=1)
    tx = c.render()
    d.sprite(tx, (300 + i * 440, 640), (700, 700 * 1400 / 1024), target=fbo, uOutline=6, uOutlineColor=(1, 1, 1))
tb = TextBatch(); s = 150
xs, wd = layout(at, '全部がpotatoになっていく', s)
for ch, x in zip('全部がpotatoになっていく', xs):
    tb.glyph(at, ch, W/2 - wd/2 + x, 180, s, fill=(1, .85, .3, 1), fill2=(1, .3, .6, 1), line=(.15, .05, .2, 1), outline=.18, glow=.8, sweep=0.5)
txt.render(tb.data(), {'uAtlas': at.tex}, target=fbo)
Image.fromarray(e.read(fbo)).save('D:/MV_DS/work/test_engine.png')
t0 = time.time()
for i in range(30):
    for k, c in chars.items(): c.pose(i/30, 1/30, mouth=.5); c.render()
    e.read(fbo)
print('4 l2d + readback per frame ms', (time.time() - t0) / 30 * 1000)
