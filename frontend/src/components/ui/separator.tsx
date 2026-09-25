"use client";
import * as SeparatorPrimitive from "@radix-ui/react-separator";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";
export function Separator({ className, ...props }: ComponentProps<typeof SeparatorPrimitive.Root>) { return <SeparatorPrimitive.Root className={cn("reference-separator", className)} decorative {...props}/>; }
