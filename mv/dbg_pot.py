import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, math
from PIL import Image
from director.mv import MV
from director.common import screen_xy, potato_uniforms
mv = MV(); mv.t = 185.0
mv.cur = mv.scene_fbo; mv.scene_fbo.use(); mv.ctx.clear(0, 0, 0, 1)
for z in (1.0, 2.2):
    fb = mv.e.target(f's{z}')[0]
    mv.cur = fb; fb.use(); mv.ctx.clear(0, 0, 0, 1)
    mv.potatoes([((0, 0, z), .62, (0, 1, 0), 1.0, 14., 1.)], rim=(1, .8, .5))
    img = mv.e.read(fb)[..., :3]
    print(z, 'mean', round(float(img.mean()), 1), 'max', int(img.max()), 'screen', [round(v) for v in screen_xy(0, 0, z)])
    Image.fromarray(img).resize((640, 360)).save(f'D:/MV_DS/work/dbg_pot_{z}.jpg')
