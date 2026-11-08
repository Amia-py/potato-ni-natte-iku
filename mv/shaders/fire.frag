#version 330
// Stylised cartoon flames rising from the bottom + embers. Output premultiplied (transparent where no fire).
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform float uHeight;    // flame height (0..1.2 of screen)
uniform float uIntensity;
uniform float uBeat;
uniform vec3 uInner;      // core colour
uniform vec3 uOuter;      // edge colour

void main() {
    float asp = uResolution.x / uResolution.y;
    vec2 p = vec2(uv.x * asp, uv.y);
    float h = uHeight * (1. + .15 * uBeat);
    // turbulent upward flow
    vec2 q = vec2(p.x * 3., p.y * 2. - uTime * 2.2);
    float n = fbm(q + vec2(fbm(q * 1.3 + uTime * .5), 0.) * 1.2);
    // tongues: columns of different heights
    float col = p.x * 5.;
    float tongue = (.55 + .45 * vnoise(vec2(floor(col) * 1.7, floor(uTime * 3.) * .3 + floor(col)))) ;
    float shape = h * (.6 + .5 * n) * (.75 + .25 * sin(p.x * 9. + uTime * 4.) * sin(p.x * 3.7 - uTime * 3.));
    float d = uv.y - shape;
    float flame = smoothstep(.03, -.03, d);
    float core = smoothstep(-.05, -.25, d - .02 * n);
    vec3 c = mix(uOuter, uInner, core);
    c = mix(c, vec3(1., .98, .85), smoothstep(-.25, -.5, d) * .8);
    // toon banding
    c = floor(c * 4.) / 4. + .1;
    float a = flame * uIntensity;
    // embers
    vec2 ep = vec2(p.x * 14., p.y * 7. - uTime * 3.);
    vec2 ec = floor(ep); vec2 ef = fract(ep) - .5;
    vec2 eo = hash22(ec) - .5;
    float ember = smoothstep(.09, .0, length(ef - eo * .6)) * step(.82, hash21(ec + 3.)) * smoothstep(h * 1.6, h * .3, uv.y);
    vec3 outc = c * a + vec3(1., .6, .2) * ember * uIntensity * 1.5;
    float oa = max(a, ember * uIntensity);
    fragColor = vec4(outc, oa);
}
