#version 330
// Manga / comic backgrounds: radial speed lines, concentration burst, halftone gradient, stripes.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform vec3 uColA;
uniform vec3 uColB;
uniform float uMode;      // 0 radial burst, 1 speed lines horizontal, 2 rotating sunburst stripes, 3 halftone gradient
uniform vec2 uFocus;      // 0..1
uniform float uBeat;
uniform float uSpin;

void main() {
    float asp = uResolution.x / uResolution.y;
    vec2 p = (uv - uFocus) * vec2(asp, 1.);
    float r = length(p), a = atan(p.y, p.x);
    vec3 col = uColA;
    if (uMode < .5) {
        float rays = vnoise(vec2(a * 40., floor(uTime * 12.)));
        float lines = step(.62 - .1 * uBeat, rays) * smoothstep(.12, .5, r);
        col = mix(uColA, uColB, lines);
    } else if (uMode < 1.5) {
        float y = uv.y * 90.;
        float l = vnoise(vec2(floor(y), floor(uTime * 20.)));
        float len = fract(uv.x * (1. + l) * 1.5 + uTime * (3. + 4. * l) + l * 7.);
        col = mix(uColA, uColB, step(.7, l) * step(.35, len));
    } else if (uMode < 2.5) {
        float st = step(.5, fract((a + uTime * uSpin) / TAU * 18.));
        col = mix(uColA, uColB, st);
        col *= 1. - .25 * smoothstep(.2, 1.2, r);
    } else {
        float h = halftone(gl_FragCoord.xy, 14., .785, smoothstep(0., 1.2, r));
        col = mix(uColA, uColB, h);
    }
    col *= .95 + .1 * uBeat;
    fragColor = vec4(col, 1.);
}
