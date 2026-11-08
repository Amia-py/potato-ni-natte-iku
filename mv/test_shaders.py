import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from engine.gl import Engine
W, H = 1920, 1080
e = Engine(W, H)
scene, stex = e.target('scene'); bl1, b1 = e.target('bl1', W // 4, H // 4); bl2, b2 = e.target('bl2', W // 4, H // 4)
out, otex = e.target('out', dtype='f1')
def post(name, **u):
    e.pass_('blur.frag', bl1, {'uSrc': stex}, uDir=(1., 0.), uThresh=0.7)
    e.pass_('blur.frag', bl2, {'uSrc': b1}, uDir=(0., 1.), uThresh=-1.)
    d = dict(uBloomAmt=.8, uCA=1., uGrain=.04, uVignette=.6, uFlash=(1, 1, 1, 0), uCrumple=0., uBallScale=1., uBallRot=0.,
             uBallOff=(0., 0.), uBg=(.1, .05, .15), uHalftone=0., uSat=1.1, uContrast=1.05, uTint=(1, 1, 1), uLetterbox=0., uShake=(0., 0.), uMono=0., uTime=1.)
    d.update(u)
    e.pass_('post.frag', out, {'uScene': stex, 'uBloom': b2}, **d)
    Image.fromarray(e.read(out)[..., :3]).save(f'D:/MV_DS/work/shot_{name}.png')
# 1 stage
e.pass_('stage.frag', scene, uTime=3., uCurtain=.7, uWall=(.35, .12, .5), uCurtainCol=(.55, .04, .1),
        uSpot=[.3, .45, .18, 1., .7, .55, .18, 1., .5, .5, .25, .7, 0, 0, 0, 0], uSpotCol=[1, .8, .4, .5, .7, 1, 1, .5, .9, 0, 0, 0],
        uBulbs=1., uChase=1., uGrave=1., uMoon=1., uBeat=.5, uHaze=1.)
post('stage')
# 2 stew + potatoes
e.pass_('stew.frag', scene, uTime=5., uColA=(.35, .08, .02), uColB=(.95, .45, .12), uColC=(1., .85, .5), uSwirl=1., uBubble=.8,
        uBeat=.5, uHeat=.6, uFlow=0., uZoom=1., uCenter=(.5, .5))
rng = np.random.RandomState(3); n = 18
pot = []; rot = []; info = []
for i in range(n):
    pot += [rng.uniform(-3, 3), rng.uniform(-1.6, 1.6), rng.uniform(-2, 1), rng.uniform(.25, .5)]
    rot += list(rng.normal(size=3)) + [rng.uniform(0, 6)]
    info += [rng.uniform(0, 10), float(i % 3 == 0), 0., 0.]
e.pass_('potatoes.frag', scene, blend=True, uTime=1., uCount=n, uPot=pot, uRot=rot, uInfo=info, uRim=(1., .4, .8), uKeyDir=(-.5, .8, .6), uExposure=1.)
post('stew')
post('crumple', uCrumple=.6)
