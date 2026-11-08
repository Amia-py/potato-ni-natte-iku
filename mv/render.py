"""Render driver.
  python render.py stills 10.5 60 ...        -> <root>/work/stills/f_<t>.png
  python render.py sheet  t0 t1 n             -> contact sheet of n frames between t0..t1
  python render.py video  out.mp4 [t0 t1] [--fps 60] [--scale 1]
"""
import sys, os, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import imageio_ffmpeg

from director.mv import MV

FF = imageio_ffmpeg.get_ffmpeg_exe()
# project root derived from this file, so the tree can be moved without editing paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
MUSIC = f'{ROOT}/music.m4a'


def warm(mv, t, n=20, fps=60):
    """run a few frames before t so Live2D physics / blinking settle"""
    for k in range(n, 0, -1):
        mv.frame(max(0., t - k / fps))


def stills(ts):
    mv = MV(); os.makedirs(f'{ROOT}/work/stills', exist_ok=True)
    for t in ts:
        warm(mv, t, 10)
        fb = mv.frame(t)
        Image.fromarray(mv.e.read(fb)[..., :3]).save(f'{ROOT}/work/stills/f_{t:07.2f}.png')
        print('still', t, flush=True)


def sheet(t0, t1, n, out, cols=4, tw=480):
    mv = MV()
    ts = np.linspace(t0, t1, n)
    th = tw * 9 // 16
    rows = (n + cols - 1) // cols
    S = Image.new('RGB', (cols * tw, rows * th), (0, 0, 0))
    for i, t in enumerate(ts):
        warm(mv, t, 6)
        im = Image.fromarray(mv.e.read(mv.frame(t))[..., :3]).resize((tw, th), Image.LANCZOS)
        S.paste(im, (i % cols * tw, i // cols * th))
    S.save(out, quality=88)
    print('sheet', out)


def video(out, t0=0.0, t1=None, fps=60, crf=21):
    mv = MV()
    t1 = t1 if t1 is not None else mv.au.dur
    n = int(round((t1 - t0) * fps))
    cmd = [FF, '-y', '-hide_banner', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{mv.W}x{mv.H}', '-r', str(fps), '-i', '-',
           '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', MUSIC,
           '-map', '0:v', '-map', '1:a', '-vf', 'vflip',
           '-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', str(crf), '-b:v', '14M', '-maxrate', '22M', '-bufsize', '44M', '-profile:v', 'high',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    mv.dt = 1 / fps
    warm(mv, t0, 10, fps)
    st = time.time()
    for i in range(n):
        t = t0 + i / fps
        fb = mv.frame(t)
        p.stdin.write(fb.read(components=4, dtype='f1'))   # GL rows are bottom-up; ffmpeg vflips
        if i % 300 == 0:
            el = time.time() - st
            print(f'frame {i}/{n} t={t:.2f} {i / max(el, 1e-6):.1f} fps', flush=True)
    p.stdin.close(); p.wait()
    print('done', out, f'{time.time() - st:.0f}s')


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        stills([float(x) for x in sys.argv[2:]])
    elif mode == 'sheet':
        sheet(float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else f'{ROOT}/work/sheet.jpg')
    elif mode == 'video':
        args = sys.argv[2:]
        fps = 60
        if '--fps' in args:
            i = args.index('--fps'); fps = int(args[i + 1]); del args[i:i + 2]
        out = args[0]
        t0 = float(args[1]) if len(args) > 1 else 0.0
        t1 = float(args[2]) if len(args) > 2 else None
        video(out, t0, t1, fps)
