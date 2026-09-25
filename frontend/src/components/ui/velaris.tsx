"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { cn, createDecorativeLoop } from "@/lib/utils";

const vertexShaderGLSL = `
attribute vec2 position;
varying vec2 vUv;
void main() {
  vUv = position * 0.5 + 0.5;
  gl_Position = vec4(position, 0.0, 1.0);
}`;

// Adapted from the supplied Velaris: the same layered simplex noise, glow and grain.
const fragmentShaderGLSL = `
precision highp float;
varying vec2 vUv;
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_grain;
uniform vec3 u_colors[4];
uniform vec3 u_bg;
vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
    -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
    + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw)), 0.0);
  m = m*m;
  m = m*m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
void main() {
  vec2 uv = vUv;
  float ratio = u_resolution.x / u_resolution.y;
  vec2 p = uv - 0.5;
  p.x *= ratio;
  float t = u_time * 0.1;
  float n1 = snoise(p * 0.4 + vec2(t * 0.2, -t * 0.3));
  float n2 = snoise(p * 0.55 + vec2(-t * 0.15, t * 0.25) + n1 * 0.25);
  float n3 = snoise(p * 0.75 + vec2(t * 0.1, -t * 0.2) + n2 * 0.2);
  vec3 col = u_bg;
  float dist = length(p) * 1.5;
  float vignette = 1.0 - smoothstep(0.3, 1.2, dist);
  col = mix(col, u_colors[0], smoothstep(-0.2, 0.5, n1) * 0.85);
  col = mix(col, u_colors[1], smoothstep(-0.1, 0.6, n2) * 0.7);
  col = mix(col, u_colors[2], smoothstep(-0.3, 0.4, n3) * 0.6);
  col = mix(col, u_colors[3], smoothstep(0.0, 0.7, n1 * n2) * 0.5);
  float glow = (1.0 - smoothstep(0.0, 0.8, dist)) * 0.3;
  col += u_colors[1] * glow;
  col = mix(col * 0.2, col, vignette);
  float grain = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453 + u_time);
  col += (grain - 0.5) * u_grain * 0.1;
  gl_FragColor = vec4(col, 1.0);
}`;

export interface VelarisProps {
  bg?: string;
  colors?: string[];
  speed?: number;
  grain?: number;
  height?: string;
  className?: string;
  children?: ReactNode;
}

const DEFAULT_COLORS = ["#fafafa", "#a3a3a3", "#343434", "#000000"];

function hexToRgb(value: string): [number, number, number] {
  const short = /^#([\da-f])([\da-f])([\da-f])$/i.exec(value);
  const hex = short
    ? `${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`
    : value.replace(/^#/, "");
  if (!/^[\da-f]{6}$/i.test(hex)) return [0, 0, 0];
  return [0, 2, 4].map(
    (offset) => parseInt(hex.slice(offset, offset + 2), 16) / 255,
  ) as [number, number, number];
}

export default function Velaris({
  bg = "#000000",
  colors = DEFAULT_COLORS,
  speed = 1,
  grain = 0.24,
  height = "100%",
  className,
  children,
}: VelarisProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const paletteKey = Array.from(
    { length: 4 },
    (_, index) => colors[index] ?? DEFAULT_COLORS[index],
  ).join(",");

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    let gl: WebGLRenderingContext | null;
    try {
      gl = canvas.getContext("webgl", {
        alpha: false,
        antialias: false,
        depth: false,
        stencil: false,
        powerPreference: "low-power",
      });
    } catch {
      return;
    }
    if (!gl) return; // The CSS gradient remains visible if WebGL is unavailable.
    const context = gl;
    let program: WebGLProgram | null = null;
    let buffer: WebGLBuffer | null = null;
    const shaders: WebGLShader[] = [];
    let animation: ReturnType<typeof createDecorativeLoop> | undefined;
    let draw = (_elapsed: number, _delta: number) => {};
    const safeSpeed = Number.isFinite(speed)
      ? Math.max(0, Math.min(speed, 3))
      : 1;
    const safeGrain = Number.isFinite(grain)
      ? Math.max(0, Math.min(grain, 1))
      : 0.24;

    function release() {
      animation?.dispose();
      animation = undefined;
      if (buffer) context.deleteBuffer(buffer);
      if (program) context.deleteProgram(program);
      shaders.splice(0).forEach((shader) => context.deleteShader(shader));
      buffer = null;
      program = null;
      draw = () => {};
      delete canvas!.dataset.ready;
    }

    function compile(type: number, source: string) {
      const shader = context.createShader(type);
      if (!shader) throw new Error("Shader unavailable");
      shaders.push(shader);
      context.shaderSource(shader, source);
      context.compileShader(shader);
      if (!context.getShaderParameter(shader, context.COMPILE_STATUS))
        throw new Error("Shader compilation failed");
      return shader;
    }

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const width = Math.max(1, Math.round(container!.clientWidth * dpr));
      const height = Math.max(1, Math.round(container!.clientHeight * dpr));
      if (canvas!.width !== width || canvas!.height !== height) {
        canvas!.width = width;
        canvas!.height = height;
      }
      context.viewport(0, 0, width, height);
      animation?.invalidate();
    }

    function initialize() {
      release();
      try {
        program = context.createProgram();
        if (!program) throw new Error("WebGL program unavailable");
        const precision = context.getShaderPrecisionFormat(
          context.FRAGMENT_SHADER,
          context.HIGH_FLOAT,
        );
        const fragment = precision?.precision
          ? fragmentShaderGLSL
          : fragmentShaderGLSL.replace(
              "precision highp float;",
              "precision mediump float;",
            );
        context.attachShader(
          program,
          compile(context.VERTEX_SHADER, vertexShaderGLSL),
        );
        context.attachShader(
          program,
          compile(context.FRAGMENT_SHADER, fragment),
        );
        context.linkProgram(program);
        if (!context.getProgramParameter(program, context.LINK_STATUS))
          throw new Error("Shader linking failed");
        context.useProgram(program);
        buffer = context.createBuffer();
        if (!buffer) throw new Error("WebGL buffer unavailable");
        context.bindBuffer(context.ARRAY_BUFFER, buffer);
        context.bufferData(
          context.ARRAY_BUFFER,
          new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
          context.STATIC_DRAW,
        );
        const position = context.getAttribLocation(program, "position");
        if (position < 0) throw new Error("Shader position unavailable");
        context.enableVertexAttribArray(position);
        context.vertexAttribPointer(position, 2, context.FLOAT, false, 0, 0);
        const resolution = context.getUniformLocation(program, "u_resolution");
        const time = context.getUniformLocation(program, "u_time");
        context.uniform1f(
          context.getUniformLocation(program, "u_grain"),
          safeGrain,
        );
        context.uniform3f(
          context.getUniformLocation(program, "u_bg"),
          ...hexToRgb(bg),
        );
        context.uniform3fv(
          context.getUniformLocation(program, "u_colors[0]"),
          new Float32Array(paletteKey.split(",").flatMap(hexToRgb)),
        );
        draw = (elapsed) => {
          if (context.isContextLost()) return;
          context.uniform2f(resolution, canvas!.width, canvas!.height);
          context.uniform1f(time, elapsed * safeSpeed);
          context.drawArrays(context.TRIANGLE_STRIP, 0, 4);
        };
        resize();
        animation = createDecorativeLoop(
          container!,
          draw,
          () => safeSpeed > 0 && !context.isContextLost(),
        );
        canvas!.dataset.ready = "true";
      } catch {
        release(); // Keep the local static CSS fallback, including on shader failure.
      }
    }

    const lost = (event: Event) => {
      event.preventDefault();
      release();
    };
    const restored = () => initialize();
    canvas.addEventListener("webglcontextlost", lost);
    canvas.addEventListener("webglcontextrestored", restored);
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    initialize();
    return () => {
      resizeObserver.disconnect();
      canvas.removeEventListener("webglcontextlost", lost);
      canvas.removeEventListener("webglcontextrestored", restored);
      release();
    };
  }, [bg, paletteKey, speed, grain]);

  return (
    <div
      ref={containerRef}
      className={cn("velaris", className)}
      style={{ height }}
    >
      <canvas ref={canvasRef} className="velaris-canvas" aria-hidden="true" />
      {children && <div className="velaris-content">{children}</div>}
    </div>
  );
}
