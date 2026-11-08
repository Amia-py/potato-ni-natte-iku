#version 330
// Transition between uA (outgoing) and uB (incoming).
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform sampler2D uA;
uniform sampler2D uB;
uniform float uProg;
uniform float uMode;     // 0 star, 1 iris, 2 melt, 3 slash, 4 crossfade, 5 pixel,
                         // 6 film burn, 7 projector roll, 8 flash cut, 9 shutter bar,
                         // 10 slice slide, 11 negative flash, 12 grid dissolve, 13 push
uniform vec2 uFocus;
uniform float uTime;

void main() {
    float asp = uResolution.x / uResolution.y;
    vec2 p = (uv - uFocus) * vec2(asp, 1.);
    vec4 a = texture(uA, uv), b = texture(uB, uv);
    float m = 0.; float edge = 0.;
    float t = uProg;
    if (uMode < .5) {
        float d = sdStar5(rot2(t * 2.) * p, t * 2.4, .45);
        m = smoothstep(.004, -.004, d); edge = smoothstep(.03, 0., abs(d));
    } else if (uMode < 1.5) {
        float d = length(p) - t * 1.3;
        m = smoothstep(.004, -.004, d); edge = smoothstep(.02, 0., abs(d));
    } else if (uMode < 2.5) {
        float col = floor(uv.x * 30.);
        float drip = t * 1.6 - (.3 + .5 * hash11(col)) * .6 - .25 * (1. - sin(fract(uv.x * 30.) * PI));
        m = step(1. - uv.y, drip);
        vec2 sh = vec2(0., drip * .3);
        a = texture(uA, uv + sh * step(drip, 1. - uv.y));
    } else if (uMode < 3.5) {
        float d = (uv.x - .5) * asp + (uv.y - .5) * .6 - (t * 2.6 - 1.3) * asp * .6;
        m = smoothstep(.004, -.004, d); edge = smoothstep(.015, 0., abs(d));
    } else if (uMode < 4.5) {
        m = t;
    } else if (uMode < 5.5) {
        vec2 c = floor(uv * vec2(48., 27.));
        m = step(hash21(c), t);
    } else if (uMode < 6.5) {
        // film burn: a hole burns outward through the frame, charred at the lip
        float d = length((uv - .5) * vec2(asp, 1.));
        float n = fbm(uv * 5. + uTime * .15) - .5;
        float r = t * 1.35;
        m = smoothstep(-.02, .02, r - (d + n * .16));
        edge = smoothstep(.11, 0., abs(d + n * .16 - r));
    } else if (uMode < 7.5) {
        // projector slip: a clean vertical wipe with a hairline seam and a little frame slip
        float slip = (t * 8. - 4.);
        a = texture(uA, vec2(uv.x, uv.y + slip / uResolution.y));
        b = texture(uB, vec2(uv.x, uv.y - slip / uResolution.y));
        float seam = 1. - t;
        m = smoothstep(seam + .012, seam - .012, uv.y);
        edge = smoothstep(.012, 0., abs(uv.y - seam));
    } else if (uMode < 8.5) {
        // flash cut: a two-frame blowout carries the change
        m = step(.5, t);
        edge = exp(-abs(t - .5) * 9.);
    } else if (uMode < 9.5) {
        // shutter bar sweeps the frame
        float b = smoothstep(0., .06, abs(uv.y - (1. - t)));
        m = b;
        edge = smoothstep(.02, 0., abs(uv.y - (1. - t)));
    } else if (uMode < 10.5) {
        // slice slide: the frame is cut into bands, each slips at its own speed
        float rows = 14.;
        float row = floor(uv.y * rows);
        float hsh = hash11(row * 7.13);
        float off = (t * (1.4 + hsh * 2.6) - .55) * (hsh > .5 ? 1. : -1.);
        a = texture(uA, uv + vec2(off * .35, 0.));
        b = texture(uB, uv - vec2(off * .55, 0.));
        float lead = clamp(t * 1.9 - (1. - hsh) * .55, 0., 1.);
        m = step(lead, 1. - abs(off) * .8);
        edge = smoothstep(.02, 0., abs(fract(uv.y * rows) - .5) - .46) * (1. - abs(t - .5) * 2.) * .5;
    } else if (uMode < 11.5) {
        // negative flash: the print is struck, inverts, then lands on the new frame
        float f = smoothstep(0., .16, t) * (1. - smoothstep(.18, .34, t));
        vec3 src = mix(a.rgb, 1. - a.rgb, f);
        vec3 dst = mix(1. - b.rgb, b.rgb, smoothstep(.30, .52, t));
        fragColor = vec4(t < .40 ? src : dst, 1.);
        return;
    } else if (uMode < 12.5) {
        // grid dissolve: cells snap in on a diagonal, a hairline lattice holds them
        vec2 g = vec2(24., 14.);
        vec2 c = floor(uv * g) / g;
        float key = (c.x * .55 + (1. - c.y) * .75) * .62;
        m = step(key, t * 1.02);
        vec2 fr = fract(uv * g);
        float lat = smoothstep(.46, .5, max(fr.x, fr.y));
        edge = lat * (1. - abs(t * 2. - 1.)) * .8;
    } else {
        // push: the outgoing frame slides out and drags the incoming one in
        a = texture(uA, uv + vec2(t * .92, 0.));
        b = texture(uB, uv - vec2((1. - t) * .92, 0.));
        m = step(uv.x, t);
        edge = smoothstep(.006, 0., abs(uv.x - t)) * .6;
    }
    vec4 o = mix(a, b, m);
    float amber = (uMode > 6.5 && uMode < 7.5) ? 0. : 1.5;
    if (uMode > 11.5 && uMode < 12.5) amber = 0.;            // the lattice is ink, not light
    o.rgb += vec3(1., .85, .3) * edge * amber;
    if (uMode > 11.5 && uMode < 12.5) o.rgb = mix(o.rgb, vec3(.10, .09, .07), edge * .40);
    if (uMode > 6.5 && uMode < 7.5) o.rgb *= 1. - edge * .45;   // a soft dark seam, no blow-out
    if (uMode > 5.5 && uMode < 6.5) {
        o.rgb += vec3(1., .52, .14) * edge * 1.2;      // burning edge glows amber
        o.rgb *= 1. - .45 * smoothstep(.16, .02, abs(length((uv - .5) * vec2(asp, 1.)) - t * 1.35) - .16);
    }
    if (uMode > 7.5 && uMode < 8.5) o.rgb += vec3(1., .95, .82) * edge * 2.2;
    fragColor = o;
}
