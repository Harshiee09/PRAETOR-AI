"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu";

/** Adapted from the supplied Header1 reference, with the product's actual routes. */
export function Header1({ children }: { children?: ReactNode }) {
  const pathname = usePathname();
  return <header className="product-header">
    <Link href="/" className="product-brand" aria-label="PRAETOR AI home"><span className="product-monogram" aria-hidden="true">P<span>·</span></span><span>PRAETOR<span className="product-brand-ai"> AI</span><small>INDIAN LAW. IN CONTEXT.</small></span></Link>
    <NavigationMenuPrimitive.Root className="top-navigation" aria-label="Main navigation">
      <NavigationMenuPrimitive.List className="top-navigation-list">
        {[{ href: "/", label: "Ask" }, { href: "/document", label: "Your document" }, { href: "/about", label: "About" }].map(item => <NavigationMenuPrimitive.Item key={item.href}><NavigationMenuPrimitive.Link asChild active={pathname === item.href}><Link className="top-nav-link" href={item.href} aria-current={pathname === item.href ? "page" : undefined}>{item.label}</Link></NavigationMenuPrimitive.Link></NavigationMenuPrimitive.Item>)}
      </NavigationMenuPrimitive.List>
    </NavigationMenuPrimitive.Root>
    <div className="product-header-actions">{children}</div>
  </header>;
}
