"""Cubism .motion3.json (L2D motion) -> sampled parameter values."""
import json
import numpy as np


class Motion3:
    def __init__(self, path):
        d = json.load(open(path, encoding='utf-8'))
        self.name = path.replace('\\', '/').split('/')[-1].replace('.motion3.json', '')
        self.duration = float(d.get('Meta', {}).get('Duration', 0.))
        self.loop = bool(d.get('Meta', {}).get('Loop', False))
        self.curves = {}
        for c in d.get('Curves', []):
            if c.get('Target') != 'Parameter':
                continue
            seg = c['Segments']
            if len(seg) < 2: continue
            pts = [(seg[0], seg[1])]
            i = 2
            while i < len(seg):
                kind = seg[i]
                if kind in (1, 2, 3) and i + 6 < len(seg):      # bezier / stepped / bezier-3 handle pairs
                    pts.append((seg[i + 1], seg[i + 2])); i += 7
                elif kind == 3 and i + 4 < len(seg):
                    pts.append((seg[i + 1], seg[i + 2])); i += 5
                elif i + 2 < len(seg):                          # linear (or truncated tail)
                    pts.append((seg[i + 1], seg[i + 2])); i += 3
                else:
                    break
            if len(pts) > 1:
                ts = np.array([p[0] for p in pts], dtype=np.float64)
                vs = np.array([p[1] for p in pts], dtype=np.float64)
                o = np.argsort(ts, kind='stable'); ts, vs = ts[o], vs[o]
                self.curves[c['Id']] = (ts, vs)

    def sample(self, t):
        if self.duration > 0: t = min(max(t, 0.), self.duration)
        return {k: float(np.interp(t, ts, vs)) for k, (ts, vs) in self.curves.items()}
