import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
export function Badge({ className, variant = "default", ...props }: HTMLAttributes<HTMLSpanElement> & { variant?: "default" | "outline" | "secondary" }) { return <span className={cn("reference-badge", `reference-badge-${variant}`, className)} {...props}/>; }
