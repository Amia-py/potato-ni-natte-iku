#version 330
// CRT television: draws a TV body (rounded box, knobs) and shows uScreen with curvature, scanlines,
// RGB mask, rolling bar, noise. TV rect is given in pixels (centre, size). Output premultiplied.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform sampler2D uScreen;
uniform float uTime;
uniform vec2 uCenter;     // px, y down
uniform vec2 uSize;       // px (whole TV body)
uniform float uRot;
uniform vec3 uBody;
uniform float uPower;     // 0 off .. 1 on (switch-off collapse below .3)
uniform float uNoise;
uniform float uChannel;   // flash when changing channel

void main() {
    vec2 px = vec2(uv.x, 1. - uv.y) * uResolution;
    vec2 d = rot2(uRot) * (px - uCenter);
    vec2 hs = uSize * .5;
    float body = sdRoundBox(d, hs, hs.y * .12);
    if (body > 2.) { fragColor = vec4(0.); return; }
    vec2 sh = vec2(hs.x * .78, hs.y * .80);       // screen half size
    vec2 sc = vec2(-hs.x * .08, 0.);               // screen centre offset (knob panel at right)
    float scr = sdRoundBox(d - sc, sh, sh.y * .18);
    // body shading
    vec3 col = uBody * (.75 + .25 * (1. - (d.y + hs.y) / uSize.y));
    col += .08 * smoothstep(4., 0., abs(body + 4.));
    // knobs
    vec2 kp = d - vec2(hs.x * .86, -hs.y * .35);
    col = mix(col, vec3(.15), smoothstep(1., -1., length(kp) - hs.x * .045));
    kp.y -= hs.y * .3;
    col = mix(col, vec3(.15), smoothstep(1., -1., length(kp) - hs.x * .045));
    // speaker grille
    vec2 gp = d - vec2(hs.x * .86, hs.y * .4);
    if (abs(gp.x) < hs.x * .05 && abs(gp.y) < hs.y * .25) col *= .7 + .3 * step(.5, fract(gp.y / 6.));
    if (scr < 0.) {
        // curved screen coordinates
        vec2 s = (d - sc) / sh;          // -1..1
        s *= 1. + .08 * dot(s, s);
        vec2 suv = s * .5 + .5;
        suv.y = 1. - suv.y;
        // power on/off collapse to a line then a dot
        float pw = uPower;
        float sy = smoothstep(0., .35, pw), sx = smoothstep(0., .12, pw);
        vec2 cuv = (suv - .5) / vec2(max(sx, .005), max(sy, .003)) + .5;
        vec3 img = vec3(0.);
        if (cuv.x > 0. && cuv.x < 1. && cuv.y > 0. && cuv.y < 1.) {
            float roll = .5 + .5 * sin((cuv.y + uTime * .15) * 6.);
            float j = (hash21(vec2(floor(cuv.y * 240.), floor(uTime * 30.))) - .5) * .004 * (1. + 6. * uNoise);
            img.r = texture(uScreen, cuv + vec2(j + .002, 0.)).r;
            img.g = texture(uScreen, cuv + vec2(j, 0.)).g;
            img.b = texture(uScreen, cuv + vec2(j - .002, 0.)).b;
            img *= .85 + .15 * sin(cuv.y * uResolution.y * 1.4);        // scanlines
            float m = mod(gl_FragCoord.x, 3.);
            img *= vec3(m < 1. ? 1.1 : .9, m >= 1. && m < 2. ? 1.1 : .9, m >= 2. ? 1.1 : .9);
            img *= .9 + .1 * roll;
            img = mix(img, vec3(hash21(px + uTime)), uNoise * .5);
            img += uChannel;
            img *= 1. + (1. - sy) * 3.;
        }
        float vig = 1. - .5 * dot(s, s) * .5;
        col = img * vig + vec3(.03, .04, .05);
        col += .06 * smoothstep(.6, 0., length(s - vec2(-.5, .5)));  // glass reflection
    } else {
        col = mix(vec3(.05), col, smoothstep(0., 6., scr));          // bezel
    }
    float a = smoothstep(1., -1., body);
    fragColor = vec4(col * a, a);
}
