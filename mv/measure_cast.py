import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from engine.gl import Engine
from engine.l2d import Character
e = Engine(256, 256)
mot = {'rui': 'm-adult09-pose', 'tsukasa': 'm-proud07-pose', 'emu': 'w-adult02-pose', 'nene': 'w-adult01-pose', 'miku': 'w-cool02-pose'}
for n in ['rui', 'tsukasa', 'emu', 'nene', 'miku']:
    c = Character(e, n)
    for k in range(30): c.pose(1.0, 1 / 30, motion=mot[n], mphase=1.0)
    t = c.render(); a = np.frombuffer(t.read(), np.uint8).reshape(c.H, c.W, 4)[::-1][..., 3]
    ys = np.where(a.max(1) > 20)[0]; xs = np.where(a.max(0) > 20)[0]
    print(n, 'body h', ys.max() - ys.min(), 'top', ys.min(), 'bottom', ys.max(), 'cx', (xs.min() + xs.max()) / 2, 'canvas', c.W, c.H)
