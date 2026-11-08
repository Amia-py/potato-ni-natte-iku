#version 330
#include "common.glsl"
in vec2 vUV; in vec2 vLocal; in vec2 vImg;
out vec4 fragColor;
uniform sampler2D uTex;
uniform vec2 uTexSize;
uniform vec2 uSize;
uniform float uTime;
uniform float uOpacity;
uniform vec4 uTint;          // multiply (rgb) + mix amount to flat colour (a)
uniform vec3 uAdd;           // additive
uniform float uOutline;      // outline width in px (0 = off)
uniform vec3 uOutlineColor;
uniform float uShadow;       // drop shadow strength
uniform float uDuo;          // duotone amount
uniform vec3 uDuoA; uniform vec3 uDuoB;
uniform float uMelt;         // 0..1 drip melt
uniform float uHalftone;     // halftone amount
uniform float uMask;         // 0 none, 1 rounded rect, 2 circle, 3 star
uniform float uMaskRound;
uniform float uDesat;
uniform float uGlitch;
uniform float uWobble;       // jelly wobble
uniform vec4 uUV;
uniform vec2 uClip;          // x: cut position in image space (y down), y: 0/1 enable -> hide below

vec4 samp(vec2 uv) {
    if (uv.x < 0. || uv.x > 1. || uv.y < 0. || uv.y > 1.) return vec4(0.);
    return texture(uTex, uv);
}

void main() {
    vec2 uv = vUV;
    // jelly wobble
    if (uWobble > 0.) {
        uv += uWobble * .012 * vec2(sin(vImg.y * 9. + uTime * 7.), sin(vImg.x * 7. + uTime * 6.));
    }
    // melt: columns drip downward by different amounts
    float meltMask = 1.;
    if (uMelt > 0.) {
        // smooth drips: lower parts stretch downwards by a noise-varying amount
        float n = .65 * vnoise(vec2(vImg.x * 7., 1.)) + .35 * vnoise(vec2(vImg.x * 19., 4.));
        float d = uMelt * (.25 + .75 * n) * pow(clamp(vImg.y, 0., 1.), 1.6) * .55;
        uv.y += d;
        meltMask = 1. - smoothstep(.8, 1.05, uMelt);
    }
    if (uGlitch > 0.) {
        float row = floor(vImg.y * 40.);
        float g = step(1. - uGlitch * .5, hash21(vec2(row, floor(uTime * 24.))));
        uv.x += g * (hash21(vec2(row, 7.)) - .5) * .2 * uGlitch;
    }
    vec4 c = samp(uv);
    if (uGlitch > 0.) {
        c.r = samp(uv + vec2(.006 * uGlitch, 0.)).r;
        c.b = samp(uv - vec2(.006 * uGlitch, 0.)).b;
    }
    // outline from alpha dilation
    if (uOutline > 0.) {
        float a = 0.;
        vec2 px = uOutline / uSize * abs(uUV.zw - uUV.xy);
        for (int i = 0; i < 16; i++) {
            float ang = float(i) / 16. * TAU;
            a = max(a, samp(uv + vec2(cos(ang), sin(ang)) * px).a);
            a = max(a, samp(uv + vec2(cos(ang), sin(ang)) * px * .5).a);
        }
        vec4 o = vec4(uOutlineColor, 1.) * a;
        c = c + o * (1. - c.a);
    }
    if (uShadow > 0.) {
        float a = samp(uv + vec2(-.012, .018)).a * uShadow * .6;
        c = c + vec4(0., 0., 0.04, 1.) * a * (1. - c.a);
    }
    // colour treatments (premultiplied)
    vec3 rgb = c.a > 0. ? c.rgb / c.a : vec3(0.);
    if (uDesat > 0.) rgb = mix(rgb, vec3(luma(rgb)), uDesat);
    if (uDuo > 0.) rgb = mix(rgb, mix(uDuoA, uDuoB, smoothstep(.1, .9, luma(rgb))), uDuo);
    if (uHalftone > 0.) {
        vec2 sp = gl_FragCoord.xy;
        float l = luma(rgb);
        float h = halftone(sp, 7., .6, 1. - l);
        rgb = mix(rgb, rgb * (1. - .55 * h), uHalftone);
    }
    rgb = mix(rgb * uTint.rgb, uTint.rgb, uTint.a) + uAdd;
    float alpha = c.a * uOpacity * meltMask;
    if (uClip.y > .5) alpha *= smoothstep(uClip.x + .004, uClip.x - .004, vImg.y);   // cut by the bowl's near rim
    // masks
    vec2 m = vLocal * 2. - 1.;
    if (uMask > .5 && uMask < 1.5) alpha *= smoothstep(.01, -.01, sdRoundBox(m * uSize * .5, uSize * .5, uMaskRound));
    else if (uMask > 1.5 && uMask < 2.5) alpha *= smoothstep(.005, -.005, length(m) - 1.);
    else if (uMask > 2.5) alpha *= smoothstep(.01, -.01, sdStar5(vec2(m.x, -m.y) * vec2(uSize.x / uSize.y, 1.), .95, .45));
    fragColor = vec4(rgb * alpha, alpha);
}
