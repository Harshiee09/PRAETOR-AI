"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FlowButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  text?: string;
}

/** The supplied two-arrow / expanding-circle interaction, with native button semantics. */
export const FlowButton = forwardRef<HTMLButtonElement, FlowButtonProps>(
  (
    { text = "Explore", children, className, type = "button", ...props },
    ref,
  ) => (
    <button
      ref={ref}
      type={type}
      className={cn("flow-button", className)}
      {...props}
    >
      <ArrowRight
        className="flow-button-arrow flow-button-arrow-in"
        aria-hidden="true"
      />
      <span className="flow-button-label">{children ?? text}</span>
      <span className="flow-button-circle" aria-hidden="true" />
      <ArrowRight
        className="flow-button-arrow flow-button-arrow-out"
        aria-hidden="true"
      />
    </button>
  ),
);
FlowButton.displayName = "FlowButton";
