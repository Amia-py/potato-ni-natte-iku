#version 330
// Theatre stage: back wall, velvet curtains, scalloped valance, volumetric spotlights,
// marquee bulb frame, Halloween graveyard silhouettes, haze.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform float uCurtain;     // 0 = closed, 1 = fully open
uniform vec3 uWall;         // back wall tint
uniform vec3 uCurtainCol;
uniform vec4 uSpot[4];      // x pos (0..1), aim x (0..1), width, intensity
uniform vec3 uSpotCol[4];
uniform float uBulbs;       // marquee frame brightness
uniform float uChase;       // chase phase (beats)
uniform float uGrave;       // graveyard silhouettes amount
uniform float uMoon;
uniform float uBeat;
uniform float uHaze;
uniform float uCurtainOnly;   // 1 = transparent everywhere except curtains / valance / bulbs
uniform float uDeco;          // 0..1 art-deco rays and dot field on the back wall

// art-deco backdrop: radiating gold rays, a dotted arch, and a scattered dot lattice
vec3 deco(vec2 p, vec2 uv, float asp) {
    vec3 c = vec3(0.);
    vec2 o = vec2(0., .42);
    vec2 d = p - o;
    float ang = atan(d.y, d.x);
    float rr = length(d);
    // keep the rays and the dotted arch under the title plaque, out of the crown's way
    float keep = smoothstep(1.18, .95, rr) * smoothstep(.30, .42, rr);
    float ray = .5 + .5 * cos(ang * 22.);
    c += vec3(1., .78, .32) * pow(ray, 6.) * smoothstep(.2, 1.1, rr) * .16 * keep;
    // concentric dotted arch
    float arch = abs(rr - .55 - .02 * sin(ang * 9.));
    float dotr = smoothstep(.012, .0, arch) * step(.5, fract(ang * 60.));
    c += vec3(1., .85, .45) * dotr * .5 * keep;
    // sparse dot lattice over the whole wall
    vec2 gp = p * 34.;
    vec2 cell = fract(gp) - .5;
    float lat = smoothstep(.16, .1, length(cell)) * step(.72, hash21(floor(gp)));
    c += vec3(1., .8, .38) * lat * .35 * smoothstep(-.4, .6, uv.y);
    // deco step-motif band near the bottom
    float band = smoothstep(.012, .0, abs(uv.y - (.2 + .018 * step(.5, fract(p.x * 12.)))));
    c += vec3(1., .74, .3) * band * .35 * step(.35, hash21(vec2(floor(p.x * 12.), 3.)));
    return c;
}

vec3 curtain(vec2 p, float side, float open) {
    // p.x: 0 at stage centre edge of the curtain going outwards
    float folds = cos(p.x * 38. + sin(p.y * 2. + uTime * .5) * .6 * open) * .5 + .5;
    float sh = .35 + .65 * pow(folds, 1.5);
    vec3 c = uCurtainCol * sh;
    c += vec3(1., .8, .6) * pow(folds, 18.) * .25;
    c *= .7 + .3 * smoothstep(0., .6, p.y);
    return c;
}

void main() {
    if (uCurtainOnly > .5) {
        vec2 pc = vec2((uv.x - .5) * uResolution.x / uResolution.y, uv.y);
        float opc = clamp(uCurtain, 0., 1.);
        float cwc = mix(.56, .1, opc) * uResolution.x / uResolution.y;
        float lxc = pc.x + uResolution.x / uResolution.y * .5, rxc = uResolution.x / uResolution.y * .5 - pc.x;
        float swayc = .015 * sin(uv.y * 6. + uTime) * (1. - opc);
        vec3 c = vec3(0.); float a = 0.;
        if (lxc < cwc + swayc) { c = curtain(vec2(cwc - lxc, uv.y), -1., opc); a = 1.; }
        if (rxc < cwc - swayc) { c = curtain(vec2(cwc - rxc, uv.y), 1., opc); a = 1.; }
        float vy2 = .9 + .025 * cos(pc.x * 14.);
        if (uv.y > vy2) { c = uCurtainCol * (.55 + .35 * cos(pc.x * 60.)) * .8 + vec3(1., .75, .2) * .5 * smoothstep(.012, 0., abs(uv.y - vy2 - .01)); a = 1.; }
        fragColor = vec4(c * a, a);
        return;
    }
    vec2 fc = uv * uResolution;
    float asp = uResolution.x / uResolution.y;
    vec2 p = vec2((uv.x - .5) * asp, uv.y);       // y 0 bottom .. 1 top
    // back wall + haze gradient
    vec3 col = uWall * (.25 + .75 * smoothstep(-.2, 1.1, uv.y));
    col += uWall * .25 * fbm(vec2(p.x * 2., uv.y * 3. + uTime * .05)) * uHaze;
    if (uDeco > 0.) col += deco(p, uv, asp) * uDeco;
    // moon
    if (uMoon > 0.) {
        vec2 mp = p - vec2(.55 * asp * .5, .78);
        float m = smoothstep(.12, .115, length(mp)) - smoothstep(.12, .115, length(mp - vec2(.05, .03)));
        col += vec3(1., .95, .7) * max(m, 0.) * uMoon + vec3(1., .8, .5) * uMoon * .15 * exp(-length(mp) * 6.);
    }
    // graveyard silhouettes standing on a low hill
    if (uGrave > 0.) {
        float hillY = .17 + .025 * sin(p.x * 4.3 + 1.) + .012 * sin(p.x * 11.);
        float x = p.x * 2.6;
        float id = floor(x); float fx = (fract(x) - .5) / 2.6;
        float h = .07 + .06 * hash11(id);
        float base = .17 + .025 * sin((id + .5) / 2.6 * 4.3 + 1.);
        float stone = sdRoundBox(vec2(fx * 1.2, uv.y - base - h * .5), vec2(.055, h * .5 + .02), .045);
        float cr = min(sdBox(vec2(fx, uv.y - base - h * .7), vec2(.012, h * .7)), sdBox(vec2(fx, uv.y - base - h * 1.05), vec2(.045, .012)));
        float kind = hash11(id + 3.);
        float s = kind > .65 ? cr : (kind > .25 ? stone : 1.);
        float sil = min(s, uv.y - hillY);
        col = mix(col, vec3(.05, .02, .08), smoothstep(.003, -.003, sil) * uGrave);
    }
    // floor
    float floorY = .16;
    if (uv.y < floorY) {
        float fy = (floorY - uv.y) / floorY;
        vec3 wood = vec3(.25, .13, .07) * (.6 + .4 * sin(p.x * 60. / (1. + fy * 2.)));
        col = mix(col * .3, wood * .7, .7) * (1. - fy * .5);
    }
    // spotlights (volumetric cones from above)
    for (int i = 0; i < 4; i++) {
        if (uSpot[i].w <= 0.) continue;
        vec2 src = vec2((uSpot[i].x - .5) * asp, 1.15);
        vec2 aim = vec2((uSpot[i].y - .5) * asp, floorY);
        vec2 dir = normalize(aim - src);
        vec2 d = p - src;
        float along = dot(d, dir);
        float perp = abs(d.x * dir.y - d.y * dir.x);
        float wdt = uSpot[i].z * along;
        float cone = smoothstep(wdt, wdt * .55, perp) * step(0., along);
        float dust = .7 + .3 * fbm(vec2(perp * 9., along * 4. - uTime * .3));
        col += uSpotCol[i] * cone * uSpot[i].w * .45 * dust;
        // pool of light on the floor
        vec2 fp = (p - aim) * vec2(1., 3.2);
        col += uSpotCol[i] * uSpot[i].w * .6 * smoothstep(uSpot[i].z * 1.2, 0., length(fp));
    }
    // curtains
    float open = clamp(uCurtain, 0., 1.);
    float cw = mix(.56, .1, open) * asp;     // width of each curtain from the screen edge (overlaps when shut)
    float lx = p.x + asp * .5, rx = asp * .5 - p.x;
    float sway = .015 * sin(uv.y * 6. + uTime) * (1. - open);
    if (lx < cw + sway) col = curtain(vec2(cw - lx, uv.y), -1., open);
    if (rx < cw - sway) col = curtain(vec2(cw - rx, uv.y), 1., open);
    // valance with scallops
    float vy = .9 + .025 * cos(p.x * 14.);
    if (uv.y > vy) col = uCurtainCol * (.55 + .35 * cos(p.x * 60.)) * .8 + vec3(1., .75, .2) * .5 * smoothstep(.012, 0., abs(uv.y - vy - .01));
    // marquee bulb frame
    if (uBulbs > 0.) {
        float m = 22.;
        vec2 e = fc;
        float edgeD = min(min(e.x, uResolution.x - e.x), min(e.y, uResolution.y - e.y));
        if (edgeD < m * 2.) {
            // parametrise the border
            float per = 2. * (uResolution.x + uResolution.y);
            float s;
            if (e.y < m * 2.) s = e.x; else if (uResolution.x - e.x < m * 2.) s = uResolution.x + e.y;
            else if (uResolution.y - e.y < m * 2.) s = uResolution.x + uResolution.y + (uResolution.x - e.x);
            else s = 2. * uResolution.x + uResolution.y + (uResolution.y - e.y);
            float k = floor(s / (m * 2.)); float c = (fract(s / (m * 2.)) - .5) * m * 2.;
            float dd = length(vec2(c, edgeD - m));
            float on = .25 + .75 * step(.5, fract((k + floor(uChase * 2.)) / 3.));
            float bulb = smoothstep(m * .45, m * .3, dd);
            col = mix(col, vec3(.08, .05, .02), smoothstep(m * 2., m * 1.9, edgeD) * .0 + step(edgeD, m * 2.) * .85);
            col += vec3(1., .78, .35) * (bulb * 1.6 + exp(-dd / (m * .5)) * .5) * on * uBulbs;
        }
    }
    col *= .92 + .15 * uBeat;
    fragColor = vec4(col, 1.);
}
