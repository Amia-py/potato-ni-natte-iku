#version 330
// Final composite: frame transform (paper-ball throw), KUSHA KUSHA crumple, bloom, chromatic aberration,
// halftone, grading, flash, vignette, grain, letterbox.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform sampler2D uScene;
uniform sampler2D uBloom;
uniform float uTime;
uniform float uBloomAmt;
uniform float uCA;
uniform float uGrain;
uniform float uVignette;
uniform vec4 uFlash;        // rgb, amount
uniform float uCrumple;     // 0..1
uniform float uBallScale;   // frame scale (1 = full)
uniform float uBallRot;
uniform vec2 uBallOff;      // in screen fractions
uniform vec3 uBg;           // colour revealed behind a shrunken frame
uniform float uHalftone;
uniform float uSat;
uniform float uContrast;
uniform vec3 uTint;
uniform float uLetterbox;
uniform vec2 uShake;
uniform float uMono;
uniform float uRetro;       // 0..1 brown/cream duotone + dot screen, for the art-deco look
uniform float uLift;        // faded film blacks: 0..1
uniform vec3 uLiftCol;      // the colour the blacks sit at
uniform vec3 uBloomTint;    // halation colour

void main() {
    float asp = uResolution.x / uResolution.y;
    vec2 p = (uv - .5) * vec2(asp, 1.);
    p -= uBallOff * vec2(asp, 1.);
    p = rot2(-uBallRot) * p / max(uBallScale, 1e-3);
    vec2 q = p / vec2(asp, 1.) + .5 + uShake;
    // crumple: voronoi facets tilt the paper -> uv offsets + facet shading; edge of the sheet curls inward
    float shade = 1.;
    float inside = 1.;
    if (uCrumple > 0.) {
        // crumpled paper: facets act as tilted planes (shading), creases are thin bright/dark ridges
        float k = smoothstep(.45, 1., uCrumple);
        vec2 cp = p * (3.5 + 5. * uCrumple);
        vec3 v = voronoi(cp);
        vec3 n = normalize(vec3((hash22(vec2(v.z * 91.7, v.z * 13.3)) - .5) * 2.4 * uCrumple, 1.));
        float lit = dot(n, normalize(vec3(-.5, .6, .8)));
        float crease = smoothstep(.04, 0., v.y - v.x);
        shade = mix(1., .25 + 1.0 * lit, uCrumple) * (1. - .35 * crease * uCrumple) + .25 * crease * uCrumple * step(.5, fract(v.z * 7.));
        q += n.xy * .02 * uCrumple;
        // the sheet folds into a ball
        float ballR = mix(1.4, .38, k);
        float rr = length(p) + .06 * k * (vnoise(p * 6. + 3.) - .5);
        inside = smoothstep(ballR + .008, ballR - .008, rr);
        q = mix(q, .5 + p / (2. * ballR) + n.xy * .03 * k, k);   // whole picture squeezed into the ball
    }
    bool out_ = q.x < 0. || q.x > 1. || q.y < 0. || q.y > 1.;
    vec3 col;
    if (out_ || inside < .001) col = uBg;
    else {
        vec2 dir = (q - .5);
        float ca = uCA * .006;
        col.r = texture(uScene, q + dir * ca).r;
        col.g = texture(uScene, q).g;
        col.b = texture(uScene, q - dir * ca).b;
        col += texture(uBloom, q).rgb * uBloomAmt * uBloomTint;
        col *= shade;
        col = mix(uBg, col, inside);
    }
    // grading
    col = max(col, 0.);
    col = col / (1. + col * .12);                     // soft shoulder
    float l = luma(col);
    col = mix(vec3(l), col, uSat);
    col = (col - .5) * uContrast + .5;
    col *= uTint;
    if (uMono > 0.) col = mix(col, vec3(luma(col)) * vec3(.85, .92, 1.1), uMono);
    if (uRetro > 0.) {
        // art-deco grade: warm cast + printed dot screen, duotone only in the shadows so faces stay vivid
        float lg = luma(col);
        vec3 duo = mix(vec3(.12, .065, .032), vec3(1., .93, .74), smoothstep(.04, .92, lg));
        col = mix(col, duo, uRetro * .30 * smoothstep(.55, .05, lg));
        float h = halftone(gl_FragCoord.xy, 4.5, .3927, (1. - lg) * .85);
        col = mix(col, col * (1. - .5 * h), uRetro * .40);
        col = mix(col, col * vec3(1.07, 1.0, .86), uRetro * .6);          // warm cast
    }
    if (uHalftone > 0.) {
        float h = halftone(gl_FragCoord.xy, 6., .785, 1. - luma(col));
        col = mix(col, col * (1. - .6 * h) , uHalftone);
    }
    col = mix(col, uFlash.rgb, clamp(uFlash.a, 0., 1.));
    // faded film: pull the blacks up into a warm, slightly milky base
    if (uLift > 0.) {
        col = col * (1. - uLift * .16) + uLiftCol * uLift * .16;
        col = pow(max(col, 0.), vec3(1.06));
    }
    // vignette + grain
    vec2 vq = uv - .5;
    col *= 1. - uVignette * dot(vq, vq) * 1.6;
    col += (hash21(gl_FragCoord.xy + fract(uTime) * 100.) - .5) * uGrain;
    // letterbox
    float lb = uLetterbox * .12;
    if (uv.y < lb || uv.y > 1. - lb) col = vec3(0.);
    fragColor = vec4(clamp(col, 0., 1.), 1.);
}
