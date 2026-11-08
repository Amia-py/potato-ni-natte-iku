#version 330
// Procedural particle shapes. vParam: x = outline (0..1), y = glow, z = seed, w = spare
#include "common.glsl"
in vec2 vP; flat in float vShape; flat in vec4 vColor; flat in vec4 vParam;
out vec4 fragColor;

float sdBat(vec2 p) {
    p.x = abs(p.x);
    float body = length(p * vec2(1.6, 1.)) - .22;
    float wing = max(sdBox(p - vec2(.5, .05), vec2(.42, .2)), -(length(p - vec2(.36, -.32)) - .2));
    wing = max(wing, -(length(p - vec2(.72, -.3)) - .18));
    float ear = sdBox(rot2(.4) * (p - vec2(.1, .25)), vec2(.04, .1));
    return min(min(body, wing), ear);
}
float sdThumb(vec2 p) {   // thumbs-down fist
    float fist = sdRoundBox(p - vec2(0., .12), vec2(.42, .34), .14);
    float th = sdRoundBox(p - vec2(-.12, -.42), vec2(.12, .28), .1);
    return min(fist, th);
}
float sdButton(vec2 p) {
    float b = length(p) - .9;
    float holes = 1e9;
    for (int i = 0; i < 4; i++) { vec2 o = vec2(i % 2 == 0 ? -.25 : .25, i < 2 ? -.25 : .25); holes = min(holes, length(p - o) - .12); }
    return max(b, -holes);
}
float sdMedal(vec2 p) {
    float disc = length(p - vec2(0., -.25)) - .55;
    float ribbon = max(sdBox(p - vec2(0., .5), vec2(.35, .4)), -sdBox(rot2(.785) * (p - vec2(0., .9)), vec2(.2)));
    return min(disc, ribbon);
}

void main() {
    vec2 p = vP;
    float d;
    int s = int(vShape + .5);
    if (s == 0) d = length(p) - .9;                                 // circle / bokeh
    else if (s == 1) d = sdStar5(p, .9, .45);                       // star
    else if (s == 2) d = sdBox(p, vec2(.9, .45));                   // confetti
    else if (s == 3) d = sdBat(p);                                  // bat
    else if (s == 4) d = sdHeart(p * 1.1 + vec2(0., .5)) / 1.1;    // heart
    else if (s == 5) d = sdButton(p);                               // button (with holes)
    else if (s == 6) d = sdThumb(p);                                // thumbs down
    else if (s == 7) d = sdMedal(p);                                // medal
    else d = abs(length(p) - .7) - .12;                             // ring
    float aa = fwidth(d) * 1.2;
    float fill = smoothstep(aa, -aa, d);
    float ol = vParam.x > 0. ? smoothstep(aa, -aa, d - vParam.x * .25) : 0.;
    vec3 col = vColor.rgb;
    // simple inner shading
    col *= .85 + .25 * smoothstep(-.5, .5, p.y - p.x * .3);
    if (s == 7) {   // medal: gold disc with star, ribbon colour from vColor
        float disc = length(p - vec2(0., -.25)) - .55;
        vec3 gold = vec3(1., .78, .25) * (.8 + .3 * smoothstep(-.5, .3, p.y - p.x));
        float star = sdStar5(p - vec2(0., -.25), .3, .45);
        gold = mix(gold, vec3(1., .95, .7), smoothstep(aa, -aa, star));
        col = mix(col, gold, smoothstep(aa, -aa, disc));
    }
    vec3 olc = vec3(.08, .03, .1);
    vec3 c = mix(olc, col, fill);
    float a = max(fill, ol) * vColor.a;
    vec4 outc = vec4(c * a, a);
    if (vParam.y > 0.) {
        float g = exp(-max(d, 0.) * 4.) * vParam.y * (1. - fill);
        outc += vec4(vColor.rgb * g, g * .5) * vColor.a;
    }
    fragColor = outc;
}
