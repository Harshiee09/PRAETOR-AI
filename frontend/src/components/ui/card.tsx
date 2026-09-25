import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => <div ref={ref} className={cn("reference-card", className)} {...props}/>);
Card.displayName = "Card";
function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cn("reference-card-header", className)} {...props}/>; }
function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) { return <h3 className={cn("reference-card-title", className)} {...props}/>; }
function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) { return <p className={cn("reference-card-description", className)} {...props}/>; }
function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cn("reference-card-content", className)} {...props}/>; }
function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cn("reference-card-footer", className)} {...props}/>; }
export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
