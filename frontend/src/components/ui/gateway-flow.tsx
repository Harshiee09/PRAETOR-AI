"use client";

import { useEffect, useRef, type CSSProperties } from "react";
import { cn, createDecorativeLoop } from "@/lib/utils";

export interface GatewayFlowProps {
  mode?: "auto" | "dark" | "light";
  speed?: number;
  size?: number;
  gap?: number;
  length?: number;
  density?: number;
  strokeWidth?: number;
  opacity?: number;
  className?: string;
  style?: CSSProperties;
}

const clamp = (value: number, min: number, max: number, fallback: number) =>
  Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : fallback;
type Point = { x: number; y: number };
function bezier(t: number, p0: Point, p1: Point, p2: Point, p3: Point): Point {
  const u = 1 - t;
  return {
    x:
      u ** 3 * p0.x +
      3 * u ** 2 * t * p1.x +
      3 * u * t ** 2 * p2.x +
      t ** 3 * p3.x,
    y:
      u ** 3 * p0.y +
      3 * u ** 2 * t * p1.y +
      3 * u * t ** 2 * p2.y +
      t ** 3 * p3.y,
  };
}

/** Supplied Gateway Flow geometry, rendered locally without its embedded login page. */
export default function GatewayFlow({
  mode = "auto",
  speed = 1,
  size = 1,
  gap = 2,
  length = 1,
  density = 1,
  strokeWidth = 1,
  opacity = 1,
  className,
  style,
}: GatewayFlowProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    let context: CanvasRenderingContext2D | null;
    try {
      context = canvas.getContext("2d", { alpha: true });
    } catch {
      return;
    }
    if (!context) return;
    const ctx = context;
    const safeSpeed = clamp(speed, 0, 3, 1);
    const safeSize = clamp(size, 0.25, 3, 1);
    const safeGap = clamp(gap, 0, 12, 2);
    const safeLength = clamp(length, 0.35, 2.5, 1);
    const safeStroke = clamp(strokeWidth, 0.25, 4, 1);
    const count = Math.max(12, Math.round(80 * clamp(density, 0.15, 2.5, 1)));
    let width = 1;
    let height = 1;
    let tone = "255,255,255";
    let animation: ReturnType<typeof createDecorativeLoop> | undefined;
    // Fixed phases keep a calm, reproducible composition across navigation and resize.
    const paths = Array.from({ length: count }, (_, index) => ({
      isLeft: index % 2 === 0,
      start: (index / count) * 1.4 - 0.2,
      phase: (index * 0.61803398875) % 1,
      rate: 0.0015 + ((index * 0.41421356237) % 1) * 0.002,
    }));
    const colorMedia = window.matchMedia("(prefers-color-scheme: dark)");

    function updateMode() {
      const declared =
        document.documentElement.dataset.theme ??
        document.documentElement.dataset.scheme;
      const resolved =
        mode === "auto"
          ? declared === "light" || declared === "dark"
            ? declared
            : colorMedia.matches
              ? "dark"
              : "light"
          : mode;
      container!.dataset.mode = resolved;
      tone = resolved === "light" ? "20,20,20" : "255,255,255";
      animation?.invalidate();
    }

    function draw(elapsed: number) {
      ctx.clearRect(0, 0, width, height);
      const centerX = width / 2;
      const centerY = height / 2;
      ctx.lineWidth = 1.2 * safeSize * safeStroke;
      paths.forEach((path) => {
        const startY = path.start * height;
        const p0 = {
          x: path.isLeft
            ? centerX * (1 - safeLength)
            : width - centerX * (1 - safeLength),
          y: startY,
        };
        const p1 = {
          x: path.isLeft ? centerX * 0.5 : width - centerX * 0.5,
          y: startY,
        };
        const p2 = {
          x: path.isLeft ? centerX * 0.8 : width - centerX * 0.8,
          y: centerY,
        };
        const p3 = { x: centerX, y: centerY };
        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.bezierCurveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y);
        ctx.strokeStyle = `rgba(${tone},0.27)`;
        ctx.setLineDash([1, safeGap * 2]);
        ctx.stroke();
        ctx.setLineDash([]);
        // Original 60fps velocity expressed in seconds for consistent motion on all displays.
        const t = (path.phase + elapsed * path.rate * 60 * safeSpeed) % 1;
        const point = bezier(t, p0, p1, p2, p3);
        const particleSize = 3 * safeSize;
        ctx.fillStyle = `rgba(${tone},0.72)`;
        ctx.fillRect(
          point.x - particleSize / 2,
          point.y - particleSize / 2,
          particleSize,
          particleSize,
        );
      });
    }

    function resize() {
      width = Math.max(1, container!.clientWidth);
      height = Math.max(1, container!.clientHeight);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas!.width = Math.round(width * dpr);
      canvas!.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      animation?.invalidate();
    }

    updateMode();
    resize();
    animation = createDecorativeLoop(container, draw, () => safeSpeed > 0);
    canvas.dataset.ready = "true";
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    const themeObserver = new MutationObserver(updateMode);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme", "data-scheme", "class"],
    });
    colorMedia.addEventListener("change", updateMode);
    return () => {
      animation?.dispose();
      resizeObserver.disconnect();
      themeObserver.disconnect();
      colorMedia.removeEventListener("change", updateMode);
      delete canvas.dataset.ready;
    };
  }, [mode, speed, size, gap, length, density, strokeWidth]);

  return (
    <div
      ref={containerRef}
      className={cn("gateway-flow", className)}
      aria-hidden="true"
      data-mode={mode === "auto" ? undefined : mode}
      style={{ opacity: clamp(opacity, 0, 1, 1), ...style }}
    >
      <canvas
        ref={canvasRef}
        className="gateway-flow-canvas"
        aria-hidden="true"
      />
      <svg
        className="gateway-flow-fallback"
        viewBox="0 0 800 400"
        preserveAspectRatio="none"
        focusable="false"
        aria-hidden="true"
      >
        {Array.from({ length: 24 }, (_, index) => {
          const y = (index / 24) * 560 - 80;
          const left = index % 2 === 0;
          return (
            <path
              key={index}
              d={`M ${left ? 0 : 800} ${y} C ${left ? 200 : 600} ${y} ${left ? 320 : 480} 200 400 200`}
            />
          );
        })}
      </svg>
    </div>
  );
}
