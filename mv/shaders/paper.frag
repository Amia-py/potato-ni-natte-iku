#version 330
// Printed page ground for the showbill look: warm paper, fibre grain, hairline rules,
// optional letterpress dot screen, and an inverted ink page for the dark hits.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform vec3 uPaper;
uniform vec3 uInk;
uniform vec3 uAccent;
uniform float uMode;      // 0 = paper page, 1 = ink page
uniform float uRules;     // hairline column grid
uniform float uFrame;     // outer keyline frame
uniform float uGrain;
uniform float uVignette;
uniform float uBeat;
uniform float uHalftone;
uniform float uGlow;      // soft accent bloom on ink pages
uniform float uFilm;      // dust / scratch amount
uniform float uGrid;      // graph-paper ruling

void main() {
    vec2 px = uv * uResolution;
    float asp = uResolution.x / uResolution.y;
    vec3 col = uPaper;

    // paper fibre: long horizontal streaks + slow blotches
    float fib = vnoise(vec2(uv.x * 2.5, uv.y * 300.0));
    float fibre = fbm(vec2(uv.x * 3.0, uv.y * 90.0));
    float blot = fbm(uv * vec2(3.4, 2.8) + 11.0);
    col *= 1.0 + (fibre - .5) * .05 + (blot - .5) * .055 + (fib - .5) * .02;
    col *= 1.0 + (.5 - uv.y) * .045;                       // light falls from the top

    // hairline column grid at the thirds
    if (uRules > 0.) {
        float wx = 1.1 / uResolution.x, wy = 1.1 / uResolution.y;
        float l = 0.;
        for (int i = 1; i <= 2; i++) l = max(l, smoothstep(wx, 0., abs(uv.x - float(i) / 3.)));
        l = max(l, smoothstep(wy, 0., abs(uv.y - .088)));
        l = max(l, smoothstep(wy, 0., abs(uv.y - .912)));
        col = mix(col, uInk, l * uRules * .13);
    }

    // graph-paper ruling: a pale square lattice, the pencil-grid tell
    if (uGrid > 0.) {
        float g = 34.0;                                    // cell size in px
        vec2 q = px / g;
        vec2 fr = abs(fract(q) - .5);
        float cell = smoothstep(.5, .487, max(fr.x, fr.y));
        col = mix(col, uInk, cell * uGrid * .085);
        // every fifth line is heavier, like a squared notebook
        vec2 q5 = px / (g * 5.);
        float heavy = smoothstep(.5, .494, max(abs(fract(q5.x) - .5), abs(fract(q5.y) - .5)));
        col = mix(col, uInk, heavy * uGrid * .05);
    }

    // outer keyline frame with corner ticks
    if (uFrame > 0.) {
        float m = .045, t = 1.4 / uResolution.y;
        float d = min(min(uv.x - m, 1. - m - uv.x) * asp, min(uv.y - m, 1. - m - uv.y));
        float line = smoothstep(t, 0., abs(d));
        vec2 q = abs(vec2(uv.x - .5, uv.y - .5)) - vec2(.5 - m - .028, .5 - m - .028);
        float tick = step(max(q.x, q.y), .0001) * step(0., min(q.x, q.y)) * step(d, .0001);
        col = mix(col, uInk, max(line, tick * .0) * uFrame * .55);
    }

    if (uHalftone > 0.) {
        float h = halftone(px, 5.0, .3927, (1. - luma(col)) * .55);
        col -= h * uHalftone * .055;
    }

    // ink page: warm near-black, the light of a carbon-arc lamp, scanlines and banding
    if (uMode > 0.) {
        vec2 c = (uv - .5) * vec2(asp, 1.);
        float glow = exp(-dot(c, c) * 2.4);
        vec3 dark = mix(vec3(.042, .032, .026), vec3(.150, .098, .056), glow * .9);
        dark += uAccent * uGlow * .07 * glow;
        dark *= 1.0 - .040 * step(.5, fract(px.y * .5));
        dark *= 1.0 + (vnoise(vec2(px.x * .015, 3.)) - .5) * .13;
        dark += (hash21(px + fract(uTime) * 97.) - .5) * .030;
        col = mix(col, dark, uMode);
    }

    // film dirt: dust specks and the occasional vertical scratch
    if (uFilm > 0.) {
        float d = step(.9975, hash21(floor(px * .55) + floor(uTime * 10.) * 31.));
        col = mix(col, uInk, d * uFilm * (1. - uMode * .5) * .55);
        float sc = step(.9994, hash21(vec2(floor(uv.x * 760.), floor(uTime * 7.))));
        col = mix(col, mix(uInk, uPaper, uMode), sc * uFilm * .30);
    }

    col += uAccent * .012 * uBeat * (1. - uMode);
    vec2 vq = uv - .5;
    col *= 1. - uVignette * dot(vq, vq) * 1.15;
    col += (hash21(px + fract(uTime) * 100.) - .5) * uGrain;
    fragColor = vec4(clamp(col, 0., 1.), 1.);
}
