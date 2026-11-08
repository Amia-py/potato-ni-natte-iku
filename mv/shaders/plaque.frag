#version 330
// Art-deco marquee plaque for the title: dark inset panel, cream frame, gold rule, bulb studs, crown.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform vec2 uCenter;
uniform vec2 uSize;
uniform float uTime;
uniform float uBeat;
uniform float uReveal;      // 0..1 pop-in scale
uniform float uCrown;       // crown above the frame

void main() {
    vec2 asp = vec2(uResolution.x / uResolution.y, 1.);
    vec2 p = (vec2(uv.x, uv.y) - uCenter) * asp;
    vec2 h = uSize * .5 * uReveal;
    if (h.x < 1e-3 || h.y < 1e-3) { fragColor = vec4(0.); return; }

    float outer = sdRoundBox(p, h, h.y * .22);
    float inner = sdRoundBox(p, h * vec2(.935, .90), h.y * .17);
    float rule = sdRoundBox(p, h * vec2(.90, .84), h.y * .14);

    vec3 cream = vec3(.99, .95, .82);
    vec3 gold = vec3(1., .82, .36);
    vec3 panel = vec3(.11, .060, .030);

    vec3 c = vec3(0.); float a = 0.;
    if (outer < 0.) { c = cream; a = 1.; }
    if (inner < 0.) { c = panel; a = 1.; }
    float rl = exp(-abs(rule) * uResolution.y * 1.6);
    c += gold * rl * .9 * step(inner, 0.);
    // faint inner dot texture on the panel
    vec2 gp = p * uResolution.y * .05;
    float lat = smoothstep(.18, .1, length(fract(gp) - .5));
    c += gold * lat * .10 * step(inner, 0.);
    // cream border gets a gold wash and a soft inner shadow
    float edge = smoothstep(h.y * .06, 0., -outer);
    c = mix(c, gold * 1.02, edge * .55 * step(outer, 0.) * step(inner, -.001));
    c *= .96 + .10 * uBeat;
    // bulb studs marching along the frame
    float ring = abs(outer + h.y * .105);
    vec2 rr = p / max(h, vec2(1e-4));
    float per = (atan(rr.y, rr.x) / TAU) * 26. + (rr.x * .5 + rr.y * .5) * 18.;
    float stud = smoothstep(.42, .12, abs(fract(per) - .5));
    float on = .45 + .55 * step(.5, fract(floor(per) * .5 + floor(uTime * 3.)));
    float bd = smoothstep(h.y * .016, 0., ring);
    c += gold * bd * stud * on * 1.5;
    a = max(a, bd * stud);
    // crown above the frame
    if (uCrown > 0.) {
        float cy0 = h.y + h.y * .34;
        vec2 cp = p - vec2(0., cy0);
        float body = sdRoundBox(cp - vec2(0., -.04), vec2(h.y * .30, h.y * .09), h.y * .025);
        float t1 = length(cp - vec2(-h.y * .24, -h.y * .15)) - h.y * .11;
        float t2 = length(cp - vec2(0., -h.y * .18)) - h.y * .13;
        float t3 = length(cp - vec2(h.y * .24, -h.y * .15)) - h.y * .11;
        float cd = min(min(body, t1), min(t2, t3));
        float m = smoothstep(.007, -.007, cd) * uCrown;
        c = mix(c, gold, m);
        a = max(a, m);
    }
    fragColor = vec4(c * a, a);
}
