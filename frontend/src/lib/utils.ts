import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Canvas-only scheduler: a paused or hidden decoration does not consume frames. */
export function createDecorativeLoop(
  element: HTMLElement,
  draw: (elapsedSeconds: number, deltaSeconds: number) => void,
  animate: () => boolean = () => true,
) {
  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let visible = true;
  let disposed = false;
  let frame = 0;
  let last = 0;
  let elapsed = 0;
  const canAnimate = () =>
    !disposed &&
    visible &&
    !document.hidden &&
    !motion.matches &&
    !element.closest('[data-motion="paused"]') &&
    animate();

  const tick = (now: number) => {
    frame = 0;
    if (!canAnimate()) {
      last = 0;
      return;
    }
    const delta = last ? Math.min((now - last) / 1000, 0.05) : 0;
    last = now;
    elapsed += delta;
    draw(elapsed, delta);
    frame = requestAnimationFrame(tick);
  };
  const sync = () => {
    if (!canAnimate()) {
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      last = 0;
    } else if (!frame) frame = requestAnimationFrame(tick);
  };
  const observer =
    typeof IntersectionObserver === "undefined"
      ? null
      : new IntersectionObserver(([entry]) => {
          visible = entry.isIntersecting;
          sync();
        });
  observer?.observe(element);
  const preferences = new MutationObserver(sync);
  preferences.observe(document.documentElement, {
    attributes: true,
    subtree: true,
    attributeFilter: ["data-motion"],
  });
  motion.addEventListener("change", sync);
  document.addEventListener("visibilitychange", sync);
  draw(0, 0);
  sync();
  return {
    invalidate() {
      if (!disposed) draw(elapsed, 0);
    },
    dispose() {
      disposed = true;
      if (frame) cancelAnimationFrame(frame);
      observer?.disconnect();
      preferences.disconnect();
      motion.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
    },
  };
}
