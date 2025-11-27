"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard } from "lucide-react";

/**
 * Dashboard sidebar navigation
 *
 * Add navigation items as you build your resources.
 * See ARCHITECTURE.md for patterns on adding resources.
 *
 * Example of adding a resource:
 * {
 *   label: "Users",
 *   icon: Users,
 *   href: "/users",
 *   active: pathname === "/users",
 * }
 */
export function Sidebar() {
  const pathname = usePathname();

  const routes = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
      href: "/",
      active: pathname === "/",
    },
    // Add your resource routes here
    // Example:
    // { label: "Users", icon: Users, href: "/users", active: pathname === "/users" },
    // { label: "Products", icon: Package, href: "/products", active: pathname === "/products" },
  ];

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-background">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <LayoutDashboard className="h-6 w-6" />
          <span>Dashboard</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
        {routes.map((route) => (
          <Link
            key={route.href}
            href={route.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all hover:bg-accent",
              route.active ? "bg-accent text-accent-foreground" : "text-muted-foreground"
            )}
            aria-current={route.active ? "page" : undefined}
          >
            <route.icon className="h-4 w-4" />
            {route.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
