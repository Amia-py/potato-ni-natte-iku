import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glfw
from OpenGL import GL
from PIL import Image
import live2d
import numpy as np
from engine.gl import Engine
from engine.l2d import Character

M = 'D:/MV_DS/assets_miku/models/v2/main/21_miku/v2_21miku_wonder/21miku_wondershow2_t05.model3.json'
e = Engine(1024, 1400)
live2d.init(); live2d.glInit()
m = live2d.Model(); m.LoadModelJson(M); m.Resize(1024, 1400)
print('params', len(m.GetParamIds()))
fbo, tex = e.target('miku', 1024, 1400, dtype='f1')
for i in range(40): m.Update(1/30)
fbo.use(); e.ctx.clear(0,0,0,0)
GL.glBindVertexArray(0); GL.glUseProgram(0)
m.Draw()
fbo.use()
img = e.read(fbo)
Image.fromarray(img).save('D:/MV_DS/work/miku_default.png')
print('ok')
