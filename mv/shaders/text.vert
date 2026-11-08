#version 330
in vec2 in_pos;
in vec2 iPos; in float iSize; in float iRot; in vec4 iUV;
in vec4 iFill; in vec4 iFill2; in vec4 iLine; in vec4 iParam;
uniform vec2 uResolution;
out vec2 vUV; out vec2 vLocal;
flat out vec4 vFill; flat out vec4 vFill2; flat out vec4 vLine; flat out vec4 vParam;
void main() {
    vec2 p = vec2(in_pos.x, -in_pos.y) * iSize * .5;
    float c = cos(iRot), s = sin(iRot);
    p = vec2(c * p.x - s * p.y, s * p.x + c * p.y);
    vec2 px = iPos + p;
    gl_Position = vec4(px.x / uResolution.x * 2. - 1., 1. - px.y / uResolution.y * 2., 0., 1.);
    vLocal = vec2(in_pos.x, -in_pos.y) * .5 + .5;
    vec2 img = mix(iUV.xy, iUV.zw, vLocal);
    vUV = vec2(img.x, 1. - img.y);
    vFill = iFill; vFill2 = iFill2; vLine = iLine; vParam = iParam;
}
