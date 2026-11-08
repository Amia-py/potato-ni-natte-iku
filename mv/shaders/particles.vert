#version 330
in vec2 in_pos;
in vec2 iPos; in vec2 iSize; in float iRot; in float iShape; in vec4 iColor; in vec4 iParam;
uniform vec2 uResolution;
out vec2 vP; flat out float vShape; flat out vec4 vColor; flat out vec4 vParam;
void main() {
    vec2 p = vec2(in_pos.x, -in_pos.y) * iSize * .5;
    float c = cos(iRot), s = sin(iRot);
    p = vec2(c * p.x - s * p.y, s * p.x + c * p.y);
    vec2 px = iPos + p;
    gl_Position = vec4(px.x / uResolution.x * 2. - 1., 1. - px.y / uResolution.y * 2., 0., 1.);
    vP = vec2(in_pos.x, in_pos.y);      // -1..1, y up
    vShape = iShape; vColor = iColor; vParam = iParam;
}
