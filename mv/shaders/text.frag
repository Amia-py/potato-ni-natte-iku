#version 330
in vec2 vUV; in vec2 vLocal;
flat in vec4 vFill; flat in vec4 vFill2; flat in vec4 vLine; flat in vec4 vParam;
uniform sampler2D uAtlas;
out vec4 fragColor;
// vParam: x = outline width (sdf units, 0..0.4), y = glow, z = karaoke sweep (0..1 across the cell), w = edge softness
void main() {
    float d = texture(uAtlas, vUV).r;
    float aa = max(fwidth(d) * .7, .002) + vParam.w;
    float ow = vParam.x;
    float fill = smoothstep(.5 - aa, .5 + aa, d);
    float line = smoothstep(.5 - ow - aa, .5 - ow + aa, d);
    // karaoke sweep: left part takes fill2
    float sw = smoothstep(vParam.z - .03, vParam.z + .03, vLocal.x);
    vec4 fc = mix(vFill2, vFill, sw);
    vec3 col = mix(vLine.rgb, fc.rgb, fill);
    float a = mix(vLine.a * line, fc.a, fill);
    a = max(a, fill * fc.a);
    vec4 outc = vec4(col * a, a);
    // glow outside the outline (additive-ish, coloured like the sweep colour)
    if (vParam.y > 0.) {
        float g = smoothstep(.5 - ow - .32, .5 - ow, d) * vParam.y * (1. - line);
        vec3 gc = mix(vFill2.rgb, vFill.rgb, sw);
        outc += vec4(gc * g, g * .6);
    }
    fragColor = outc;
}
