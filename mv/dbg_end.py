import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from director.mv import MV
mv = MV()
for t in (183.0, 185.0, 186.2):
    for k in range(8): mv.frame(t - (8 - k) / 60)
    fb = mv.frame(t)
    sc = mv.e.read(mv.scene_fbo)[..., :3]
    print(t, 'scene mean', round(float(sc.mean()), 1), 'post mean', round(float(mv.e.read(fb)[..., :3].mean()), 1))
    Image.fromarray(sc).resize((640, 360)).save(f'D:/MV_DS/work/dbg_scene_{t}.jpg')
