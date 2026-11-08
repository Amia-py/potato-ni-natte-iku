#version 330
// 2D anime-style potatoes: flat cel tones, sticker outline, kawaii faces. Same interface as the old raymarcher:
// centre / radius / rotation still come from the 3D layout, depth only decides painter's order and on-screen scale.
#include "common.glsl"
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform int uCount;
uniform vec4 uPot[48];     // xyz centre, w radius
uniform vec4 uRot[48];     // axis-angle: xyz axis, w angle
uniform vec4 uInfo[48];    // x seed, y face (jack-o'-lantern carving), z squash, w glow
uniform vec3 uRim;
uniform vec3 uKeyDir;
uniform float uExposure;

float sdEll(vec2 p, vec2 r) { float k0 = length(p / r), k1 = length(p / (r * r)); return k0 * (k0 - 1.) / max(k1, 1e-5); }
float sdSeg(vec2 p, vec2 a, vec2 b) { vec2 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba) / dot(ba, ba), 0., 1.); return length(pa - ba * h); }
vec2 rot2(vec2 v, float a) { float c = cos(a), s = sin(a); return vec2(c * v.x + s * v.y, -s * v.x + c * v.y); }

vec2 radii(float seed, float sq) {
    vec2 r = vec2(1.22, .86) * (1. + .10 * vec2(hash11(seed), hash11(seed + 1.)) - .05);
    r.y *= 1. - .35 * sq; r.x *= 1. + .25 * sq;
    return r;
}

// lumpy potato outline (distance approximation)
float blob(vec2 q, vec2 r, float seed) {
    float a = atan(q.y, q.x);
    float k = 1. + .045 * sin(3. * a + seed * 2.3) + .03 * sin(5. * a - seed * 1.7) + .02 * sin(7. * a + seed);
    return sdEll(q, r * k);
}

// pixel -> the potato's own unit space; Rn = potato radius in ndc units
vec2 localQ(int i, vec2 ndc, out float Rn, out float rot, out float yaw) {
    vec3 c = uPot[i].xyz;
    float s = (6. - c.z) / 1.6;
    Rn = uPot[i].w / s;
    vec3 ax = normalize(uRot[i].xyz);
    rot = uRot[i].w * ax.z;                 // in-plane spin
    yaw = uRot[i].w * ax.y;                 // turning around: the face slides across the body
    vec2 q = rot2((ndc - c.xy / s) / Rn, rot);
    q.y /= .9 + .1 * cos(uRot[i].w * ax.x); // tumbling: squash and stretch
    return q;
}

vec4 shade(int i, vec2 ndc) {
    float Rn, rot, yaw;
    vec2 q = localQ(i, ndc, Rn, rot, yaw);
    float seed = uInfo[i].x, face = uInfo[i].y, sq = uInfo[i].z, gl = uInfo[i].w;
    vec2 r = radii(seed, sq);
    float px = 1. / (uResolution.y * Rn);
    float aal = 1.1 * px;
    float wl = max(.075, 2.6 * px);
    float d = blob(q, r, seed);
    float body = smoothstep(aal, -aal, d);
    float outer = smoothstep(aal, -aal, d - wl);
    vec2 L = rot2(normalize(uKeyDir.xy + 1e-4), rot);
    vec2 perp = vec2(-L.y, L.x);
    float hv = hash11(seed + 9.);
    vec3 cMid = vec3(.94, .70, .38) * (.94 + .12 * hv);
    vec3 cLit = vec3(1., .86, .55);
    vec3 cSha = vec3(.76, .47, .26);
    vec3 cDeep = vec3(.50, .29, .17);
    vec3 ink = vec3(.24, .11, .07);
    vec3 col = cMid;
    // two-tone cel shading: light patch + hard shadow crescent on the far side
    col = mix(col, cLit, smoothstep(aal, -aal, sdEll(q - L * .38, vec2(.62, .40))) * .9);
    float sh = smoothstep(-aal, aal, blob(q - L * .30, r, seed));
    col = mix(col, cSha, sh);
    float rimb = sh * smoothstep(.20, .0, -d);
    col = mix(col, mix(cSha, uRim, .55) * 1.1, rimb * .5);
    // anime highlight: a short oval and a dot
    col = mix(col, vec3(1., .97, .86), smoothstep(aal, -aal, sdEll(q - L * .52, vec2(.16, .075))) * (1. - sh));
    col = mix(col, vec3(1., .97, .86), smoothstep(aal, -aal, length(q - L * .52 - perp * .28) - .035) * (1. - sh));
    // skin dimples
    for (int k = 0; k < 5; k++) {
        vec3 h = hash33(vec3(seed, float(k), 7.));
        vec2 sp = vec2((h.x - .5) * 1.2, (h.y > .5 ? 1. : -1.) * (.5 + .18 * h.z));
        col = mix(col, cDeep, smoothstep(aal, -aal, sdEll(q - sp, vec2(.07, .045))) * .85);
    }
    vec2 fo = vec2(sin(yaw) * .30, 0.);
    if (face > .5) {
        // carved jack-o'-lantern face: star eyes + toothy grin, flat glowing colour with a dark edge
        vec2 p = q - fo * 1.2;
        vec2 e = vec2(abs(p.x) - .38, p.y - .18);
        float eye = sdStar5(e, .17, .5);
        float m = length(vec2(p.x * .8, p.y + .28)) - .42;
        m = max(m, -(length(vec2(p.x * .8, p.y + .05)) - .45));
        m = max(m, -sdBox(vec2(mod(p.x + .07, .14) - .07, p.y + .62), vec2(.035, .12)));
        float jd = min(eye, m);
        vec3 gc = vec3(1., .78 + .14 * sin(uTime * 9. + seed * 5.), .2) * (1. + gl);
        col = mix(col, ink, smoothstep(aal, -aal, jd - .035));
        col = mix(col, gc, smoothstep(aal, -aal, jd));
    } else {
        // kawaii face: three eye styles and three mouth styles picked by the potato's seed
        vec2 p = q - fo - vec2(0., -.02);
        int ty = int(floor(hash11(seed + 5.) * 3.));
        for (int sx = -1; sx <= 1; sx += 2) {
            float bl = sdEll(p - vec2(float(sx) * .58, -.12), vec2(.16, .085));
            col = mix(col, vec3(1., .48, .44), smoothstep(2. * aal, -2. * aal, bl) * .6);
        }
        float blink = 1. - .9 * smoothstep(.97, .995, .5 + .5 * sin(uTime * 2.1 + seed * 5.7));
        for (int sx = -1; sx <= 1; sx += 2) {
            float fx = float(sx);
            vec2 pe = p - vec2(fx * .34, .08);
            float dd;
            if (ty == 0) dd = sdEll(pe, vec2(.085, .12 * blink + .012));
            else if (ty == 1) dd = max(abs(length(pe - vec2(0., -.07)) - .11) - .026, -(pe.y + .01));
            else {
                vec2 pm = vec2(-fx * pe.x, pe.y);
                dd = min(sdSeg(pm, vec2(-.09, .09), vec2(.07, 0.)), sdSeg(pm, vec2(-.09, -.09), vec2(.07, 0.))) - .022;
            }
            col = mix(col, ink, smoothstep(aal, -aal, dd));
            if (ty == 0) {
                col = mix(col, vec3(1.), smoothstep(aal, -aal, length(pe - vec2(.03, .045 * blink)) - .032) * blink);
                col = mix(col, vec3(1.), smoothstep(aal, -aal, length(pe - vec2(-.025, -.05 * blink)) - .018) * blink);
            }
        }
        vec2 pm = p - vec2(0., -.2);
        if (ty == 1) {
            float dm = max(length(pm) - .13, pm.y);
            col = mix(col, vec3(.40, .10, .10), smoothstep(aal, -aal, dm));
            col = mix(col, vec3(1., .50, .52), smoothstep(aal, -aal, sdEll(pm - vec2(0., -.095), vec2(.07, .04))) * smoothstep(aal, -aal, dm));
            col = mix(col, ink, smoothstep(aal, -aal, abs(dm) - .016));
        } else if (ty == 0) {
            float dm = max(abs(length(pm - vec2(0., .1)) - .13) - .022, pm.y - .03);
            col = mix(col, ink, smoothstep(aal, -aal, dm));
        } else {
            vec2 p2 = vec2(abs(pm.x) - .065, pm.y - .02);
            float dm = max(abs(length(p2) - .065) - .02, p2.y);
            col = mix(col, ink, smoothstep(aal, -aal, dm));
        }
    }
    col *= uExposure * (1. + gl * .15);
    vec3 oc = mix(ink, vec3(.45, .18, .05), clamp(gl, 0., 1.) * .6);
    vec3 c = mix(oc, col, body);
    return vec4(c * outer, outer);
}

void main() {
    vec2 ndc = (uv * uResolution - .5 * uResolution) / uResolution.y;   // y up, height 1
    int i1 = -1, i2 = -1; float z1 = -1e9, z2 = -1e9;
    for (int i = 0; i < 48; i++) {
        if (i >= uCount) break;
        float Rn, rot, yaw;
        vec2 q = localQ(i, ndc, Rn, rot, yaw);
        if (dot(q, q) > 2.9) continue;
        float seed = uInfo[i].x;
        float px = 1. / (uResolution.y * Rn);
        float d = blob(q, radii(seed, uInfo[i].z), seed);
        if (d - max(.075, 2.6 * px) > 1.1 * px) continue;
        float z = uPot[i].z + float(i) * 1e-4;
        if (z > z1) { i2 = i1; z2 = z1; i1 = i; z1 = z; }
        else if (z > z2) { i2 = i; z2 = z; }
    }
    if (i1 < 0) { fragColor = vec4(0.); return; }
    vec4 a = shade(i1, ndc);
    if (i2 >= 0 && a.a < .999) a += shade(i2, ndc) * (1. - a.a);
    fragColor = a;
}
