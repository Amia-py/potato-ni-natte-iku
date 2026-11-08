#version 330
// Bubbling stew / witch cauldron surface (2D, top-down-ish), audio reactive.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform vec3 uColA;      // deep
uniform vec3 uColB;      // body
uniform vec3 uColC;      // highlight / foam
uniform float uSwirl;    // stirring strength
uniform float uBubble;   // bubble density/intensity
uniform float uBeat;     // 0..1 pulse on beats
uniform float uHeat;     // fire glow from edges
uniform float uFlow;     // downward melt flow
uniform float uZoom;
uniform vec2 uCenter;    // swirl centre (0..1)

void main() {
    vec2 p = (uv - uCenter) * vec2(uResolution.x / uResolution.y, 1.) * uZoom;
    float r = length(p), a = atan(p.y, p.x);
    // stirring: rotate more near the centre
    float sw = uSwirl * (uTime * .25 + 1.1 / (r + .35));   // static spiral twist + steady rotation
    vec2 q = rot2(sw) * p;
    q.y += uFlow * uTime * .25;
    // domain warp
    vec2 w = vec2(fbm(q * 2.1 + uTime * .12), fbm(q * 2.1 - uTime * .1 + 5.2));
    float f = fbm(q * 2.6 + w * 1.8 + vec2(0., uTime * .05));
    vec3 col = mix(uColA, uColB, smoothstep(.25, .75, f));
    // creamy streaks
    float streak = smoothstep(.55, .62, fbm(q * 5. + w * 3.));
    col = mix(col, uColC, streak * .35);
    // bubbles: voronoi cells, each has its own life cycle
    for (int L = 0; L < 2; L++) {
        float sc = L == 0 ? 6. : 11.;
        vec2 bq = (rot2(sw * .25) * p + vec2(0., uFlow * uTime * .25)) * sc + float(L) * 17.;
        vec2 cell = floor(bq), fr = fract(bq);
        for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
            vec2 g = vec2(i, j); vec2 id = cell + g;
            vec2 o = hash22(id); float ph = fract(uTime * (.25 + .35 * o.x) + o.y);
            float alive = step(1. - uBubble * (.55 + .45 * uBeat), hash21(id + floor(uTime * (.25 + .35 * o.x) + o.y)));
            float rad = (.08 + .32 * o.y) * smoothstep(0., .85, ph) * alive;
            vec2 d = g + .5 + (o - .5) * .5 - fr;
            float dist = length(d);
            float body = smoothstep(rad, rad - .04, dist);
            float ring = smoothstep(.05, 0., abs(dist - rad)) * alive;
            vec2 hl = d + vec2(.35, -.35) * rad;
            float spec = smoothstep(rad * .35, 0., length(hl)) * body;
            float pop = smoothstep(.85, 1., ph);
            col = mix(col, col * .8 + uColC * .25, body * (1. - pop));
            col += uColC * ring * .5 * (1. - pop) + vec3(1.) * spec * .6 * (1. - pop);
        }
    }
    // heat glow at the rim / bottom
    float edge = smoothstep(.35, 1.1, r / uZoom);
    col += uHeat * vec3(1., .45, .1) * edge * (.6 + .4 * fbm(vec2(a * 3., uTime * 2.)));
    col *= .9 + .25 * uBeat;
    // vignette towards pot wall
    col *= 1. - .45 * smoothstep(.6, 1.3, r / uZoom);
    fragColor = vec4(col, 1.);
}
