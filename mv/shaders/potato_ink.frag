#version 330
// Flat line-art potato: paper fill, single-weight ink contour, optional accent
// mis-registration shadow (printed offset), simple face glyphs.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform vec2 uCenter;     // px, (0,0) = top-left
uniform float uRadius;    // px
uniform float uRot;
uniform float uSeed;
uniform float uFace;      // 0 kawaii dots+smile, 1 jack, 2 sleepy, 3 blank
uniform float uSquash;    // 0..0.45 squash & stretch
uniform float uBlink;
uniform float uAlpha;
uniform vec3 uFill;
uniform vec3 uInk;
uniform vec3 uAccent;
uniform float uOffset;    // mis-registration amount

vec4 over(vec3 c, float a, vec4 dst) {
    return vec4(c * a + dst.rgb * (1. - a), a + dst.a * (1. - a));
}

void main() {
    // screen px -> local units, y down
    vec2 px = vec2(uv.x * uResolution.x, (1. - uv.y) * uResolution.y);
    vec2 p = (px - uCenter) / uRadius;
    p = rot2(uRot) * p;
    p.y *= 1.0 + uSquash * 1.1;
    p.x /= max(1.0 - uSquash * .55, .35);

    float ang = atan(p.y, p.x);
    float wob = .105 * sin(ang * 2. + uSeed * 6.28) + .055 * sin(ang * 3. - uSeed * 3.1)
              + .028 * sin(ang * 5. + uSeed * 9.7);
    float k = .88 + wob;

    vec2 q = p; q.y *= .93;
    float dBody = (length(q) - k) * uRadius;

    float lw = clamp(uRadius * .026, 2.4, 8.0);
    float body = 1. - smoothstep(-1.0, 1.0, dBody);
    float stroke = smoothstep(lw, 0., abs(dBody + lw * .35));

    vec2 po = p - vec2(uOffset, -uOffset);
    float dOff = (length(po * vec2(1., .93)) - k) * uRadius;
    float shadow = (1. - smoothstep(-1.0, 1.0, dOff)) * (1. - body);

    // ---- face (local y runs downward) ----
    float ey = mix(1., .10, uBlink);
    float face = 0.;
    if (uFace < .5) {                                // two dots + smile
        float e1 = length((p - vec2(-.30, -.07)) / vec2(1., ey)) - .072;
        float e2 = length((p - vec2(.30, -.07)) / vec2(1., ey)) - .072;
        float eyes = 1. - smoothstep(0., .012, min(e1, e2));
        vec2 mp = p - vec2(0., .05);
        float dm = abs(length(mp) - .155) - .012;
        dm = max(dm, -mp.y);
        float mouth = 1. - smoothstep(0., .012, dm);
        face = max(eyes, mouth);
    } else if (uFace < 1.5) {                        // jack: slanted eyes + zigzag
        float e1 = max(abs(p.x + .30) * .85 + abs(p.y + .07) - .105, 0.);
        float e2 = max(abs(p.x - .30) * .85 + abs(p.y + .07) - .105, 0.);
        float eyes = 1. - smoothstep(0., .03, min(e1, e2));
        float zz = abs(fract((p.x + .22) * 3.2) - .5) * .13 + .10;
        float mouth = (1. - smoothstep(0., .014, abs(p.y - zz))) * step(abs(p.x), .23) * step(p.y, .30);
        face = max(eyes, mouth);
    } else if (uFace < 2.5) {                        // sleepy line eyes
        float e1 = length(vec2(p.x + .29, (p.y + .07) * 3.5)) - .13;
        float e2 = length(vec2(p.x - .29, (p.y + .07) * 3.5)) - .13;
        float eyes = 1. - smoothstep(0., .02, min(e1, e2));
        float mouth = (1. - smoothstep(0., .012, abs(p.y - .14 - .045 * sin(p.x * 14.)))) * step(abs(p.x), .12);
        face = max(eyes, mouth);
    }

    vec4 out_ = vec4(0.);
    out_ = over(uAccent, shadow * .50, out_);
    out_ = over(uFill, body, out_);
    out_ = over(uInk, stroke, out_);
    out_ = over(uInk, face * body, out_);

    // small stem poking out of the top (local up is negative y)
    if (uSeed > .5) {
        vec2 sp = p - vec2(.06, -(k - .04));
        float stem = (1. - smoothstep(0., .013, abs(sp.x - .035 * sin(sp.y * 6.)))) * step(sp.y, 0.) * step(-.19, sp.y);
        out_ = over(uInk, stem, out_);
    }

    out_.a *= uAlpha;
    fragColor = vec4(out_.rgb * uAlpha, out_.a);
}
