#version 330
// A giant ceramic bowl seen from the front. uLayer 0 = stew surface inside (back), 1 = bowl body (front).
// The front wall (everything between the near rim arc and the bottom of the bowl) is fully opaque, so
// characters standing in the bowl are hidden from the waist down when this layer is drawn over them.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform float uLayer;
uniform vec2 uCenter;    // rim centre, 0..1 (y up)
uniform vec2 uRadius;    // rim ellipse radii in screen-height units
uniform vec3 uGlaze;
uniform vec3 uStewA; uniform vec3 uStewB;
uniform float uBeat;

void main() {
    float asp = uResolution.x / uResolution.y;
    vec2 p = vec2((uv.x - uCenter.x) * asp, uv.y - uCenter.y);   // y up
    vec2 e = p / uRadius;
    float rim = length(e) - 1.;
    float xr = clamp(p.x / uRadius.x, -1., 1.);
    float yArc = -uRadius.y * sqrt(max(0., 1. - xr * xr));       // near rim edge (lower half)
    if (uLayer > 1.5) {
        // back wall: solid pottery filling the whole rim ellipse, drawn BEFORE the cast so it never hides anybody
        vec2 eIn = p / (uRadius * vec2(.985, .97));
        float wallIn = smoothstep(.006, -.006, length(eIn) - 1.);
        vec3 wc = uGlaze * (.35 + .35 * smoothstep(-.2, 1., p.y / uRadius.y));
        float backLip = smoothstep(.035, .0, abs(rim)) * step(0., p.y);
        wc = mix(wc, uGlaze * 1.3 + .2, backLip);
        float wa = max(wallIn, backLip);
        fragColor = vec4(wc * wa, wa);
    } else if (uLayer < .5) {
        // stew surface inside the rim
        vec2 s = (p - vec2(0., -uRadius.y * .25)) / (uRadius * vec2(.94, .8));
        float inside = smoothstep(.01, -.01, length(s) - 1.);
        vec2 q = s * 3.;
        float f = fbm(q + vec2(uTime * .2, -uTime * .1) + fbm(q * 1.5 - uTime * .2));
        vec3 c = mix(uStewA, uStewB, f);
        vec3 v = voronoi(q * 1.6 + vec2(0., uTime * .3));
        float bub = smoothstep(.12, .0, abs(v.x - .25 - .08 * uBeat)) * step(.6, v.z);
        c += vec3(1., .9, .6) * bub * .5;
        c *= .75 + .25 * smoothstep(-1., 1., s.y);
        vec4 outc = vec4(c * inside, inside);
        float steam = fbm(vec2(p.x * 3., p.y * 2. - uTime * .6)) * smoothstep(0., .5, p.y + .1) * smoothstep(.9, .1, p.y);
        outc += vec4(vec3(1.) * steam * .25, steam * .2) * (1. - inside) * step(-.05, p.y);
        fragColor = outc;
    } else {
        vec2 hs = vec2(uRadius.x * 1.02, uRadius.x * 1.30);
        float bodyD = length(vec2(p.x / hs.x, min(p.y, 0.) / hs.y)) - 1.;
        float body = smoothstep(.005, -.005, bodyD) * step(p.y, yArc);
        float lip = smoothstep(.045, .0, abs(p.y - yArc)) * step(abs(p.x), uRadius.x * 1.02);
        vec3 c = uGlaze * (.52 + .48 * smoothstep(-1., .4, -p.x / uRadius.x + .3));
        c += .3 * smoothstep(.2, 0., abs(p.x / uRadius.x + .42)) * step(p.y, 0.);
        float band = smoothstep(.012, 0., abs(p.y + uRadius.y * .6 - yArc * .6));
        c = mix(c, vec3(1., .82, .3), band * .85);
        float st = sdStar5(vec2(mod(p.x + .08, .16) - .08, p.y + uRadius.y * .65 - yArc * .6), .03, .45);
        c = mix(c, vec3(1., .9, .4), smoothstep(.003, -.003, st) * step(abs(p.x), uRadius.x * .82) * step(p.y, 0.));
        float a = max(body, lip);
        c = mix(c, uGlaze * 1.35 + .18, lip);
        fragColor = vec4(c * a, a);
    }
}
