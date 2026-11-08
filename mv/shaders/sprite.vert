#version 330
in vec2 in_pos;
uniform vec2 uResolution;
uniform vec2 uCenter;      // px, origin top-left, y down
uniform vec2 uSize;        // px
uniform float uRot;        // radians, clockwise on screen
uniform vec2 uSkew;
uniform vec4 uUV;          // image-space rect (x0, y0, x1, y1), y down, 0..1
uniform float uPad;        // extra px around the quad (for outlines / glow)
out vec2 vUV;              // texture coords (v up)
out vec2 vLocal;           // 0..1 within quad incl. pad (y down)
out vec2 vImg;             // 0..1 image space (y down), may exceed range in pad
void main() {
    vec2 hs = uSize * .5 + uPad;
    vec2 p = vec2(in_pos.x, -in_pos.y) * hs;     // y down
    p.x += p.y * uSkew.x; p.y += p.x * uSkew.y;
    float c = cos(uRot), s = sin(uRot);
    p = vec2(c * p.x - s * p.y, s * p.x + c * p.y);
    vec2 px = uCenter + p;
    gl_Position = vec4(px.x / uResolution.x * 2. - 1., 1. - px.y / uResolution.y * 2., 0., 1.);
    vLocal = vec2(in_pos.x, -in_pos.y) * .5 + .5;
    vec2 q = (vLocal * 2. - 1.) * hs / (uSize * .5) * .5 + .5;   // 0..1 over the un-padded quad
    vImg = mix(uUV.xy, uUV.zw, q);
    vUV = vec2(vImg.x, 1. - vImg.y);
}
