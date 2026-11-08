"""Project SEKAI Live2D motion (.anim Unity AnimationClip JSON dump) -> sampled parameter curves.

Bindings: path = crc32("Parameters/" + ParamId). Curve order: streamed, dense, constant.
StreamedClip frame layout: time(f32) count(u32) then per key: curveIndex(u32) c0 c1 c2 c3 (f32),
value(t) = ((c0*dt + c1)*dt + c2)*dt + c3 with dt = t - keyTime.
"""
import json, zlib, struct
import numpy as np

def _f(u):
    return struct.unpack('<f', struct.pack('<I', u & 0xFFFFFFFF))[0]

class Motion:
    def __init__(self, path, param_ids):
        d = json.load(open(path, encoding='utf-8'))
        self.name = d['m_Name']
        mc = d['m_MuscleClip']
        self.duration = float(mc['m_StopTime'] - mc['m_StartTime'])
        clip = mc['m_Clip']['data']
        lookup = {zlib.crc32(('Parameters/' + p).encode()): p for p in param_ids}
        binds = [lookup.get(b['path']) for b in d['m_ClipBindingConstant']['genericBindings']]
        sc = clip['m_StreamedClip']; data = sc['data']; n_stream = sc['curveCount']
        # streamed keys per curve: list of (time, c0, c1, c2, c3)
        keys = [[] for _ in range(n_stream)]
        i = 0
        while i < len(data):
            t = _f(data[i]); cnt = data[i + 1]; i += 2
            for _ in range(cnt):
                ci = data[i]; c = [_f(x) for x in data[i + 1:i + 5]]; i += 5
                if t > -1e30 and ci < n_stream:
                    keys[ci].append((t, *c))
        dc = clip['m_DenseClip']; n_dense = dc['m_CurveCount']
        dense = np.array([_f(x) if isinstance(x, int) else x for x in dc['m_SampleArray']] if n_dense else [])
        const = [(_f(x) if isinstance(x, int) else float(x)) for x in clip['m_ConstantClip']['data']]
        self.curves = {}
        for ci, name in enumerate(binds):
            if name is None: continue
            if ci < n_stream:
                k = keys[ci]
                if k: self.curves[name] = ('s', np.array(k))
            elif ci < n_stream + n_dense:
                j = ci - n_stream
                self.curves[name] = ('d', dense.reshape(-1, n_dense)[:, j], dc['m_SampleRate'], dc['m_BeginTime'])
            else:
                self.curves[name] = ('c', const[ci - n_stream - n_dense])

    def sample(self, t):
        t = min(max(t, 0.0), self.duration)
        out = {}
        for name, c in self.curves.items():
            if c[0] == 'c':
                out[name] = c[1]
            elif c[0] == 's':
                k = c[1]; j = np.searchsorted(k[:, 0], t, side='right') - 1; j = max(j, 0)
                tk, c0, c1, c2, c3 = k[j]; dt = t - tk
                out[name] = ((c0 * dt + c1) * dt + c2) * dt + c3
            else:
                arr, sr, b = c[1], c[2], c[3]
                x = (t - b) * sr; j = int(np.clip(np.floor(x), 0, len(arr) - 1)); j2 = min(j + 1, len(arr) - 1)
                out[name] = arr[j] + (arr[j2] - arr[j]) * (x - j)
        return out
