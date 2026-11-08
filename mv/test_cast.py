import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from engine.gl import Engine
from engine.draw import Draw
from engine.l2d import Character, FIT
e = Engine(1920, 1080); d = Draw(e)
fbo, tex = e.target('t')
fbo.use(); e.ctx.clear(.06, .04, .1, 1)
names = ['rui', 'tsukasa', 'emu', 'nene', 'miku']
mot = {'rui': 'm-adult09-pose', 'tsukasa': 'm-proud07-pose', 'emu': 'w-adult02-pose', 'nene': 'w-adult01-pose', 'miku': 'w-cool02-pose'}
for i, n in enumerate(names):
    c = Character(e, n)
    print(n, len(c.motions), 'motions')
    for k in range(30): c.pose(1.0, 1/30, motion=mot[n], mphase=1.0, smile=.5)
    t = c.render(); fbo.use()
    d.sprite(t, (250 + i * 355, 620), (355 * c.fit, 355 * c.fit * c.W / c.H), target=fbo, uOutline=4, uOutlineColor=(1, 1, 1))
Image.fromarray(e.read(fbo)[..., :3]).save('D:/MV_DS/work/cast_test.png')
