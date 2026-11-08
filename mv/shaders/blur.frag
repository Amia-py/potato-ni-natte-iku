#version 330
// bright-pass + separable gaussian (uDir = (1,0) or (0,1)); uThresh < 0 disables bright pass
in vec2 uv;
out vec4 fragColor;
uniform vec2 uResolution;
uniform sampler2D uSrc;
uniform vec2 uDir;
uniform float uThresh;
void main() {
    vec2 px = uDir / uResolution;
    const float w[5] = float[](.227027, .1945946, .1216216, .054054, .016216);
    vec3 c = texture(uSrc, uv).rgb * w[0];
    for (int i = 1; i < 5; i++) {
        c += texture(uSrc, uv + px * float(i) * 1.6).rgb * w[i];
        c += texture(uSrc, uv - px * float(i) * 1.6).rgb * w[i];
    }
    if (uThresh >= 0.) c = max(c - uThresh, 0.) * 1.4;
    fragColor = vec4(c, 1.);
}
