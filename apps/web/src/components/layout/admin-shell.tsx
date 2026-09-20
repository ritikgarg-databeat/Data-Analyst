"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpen, LogOut, ScrollText, Server, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import { cn } from "@/lib/utils";

const links = [
  ["Dashboard", "/admin", BarChart3], ["Users", "/admin/users", Users],
  ["Content", "/admin/content", BookOpen], ["Audit", "/admin/audit", ScrollText],
  ["System", "/admin/system", Server],
] as const;

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  if (user && user.role !== "ADMIN") return <main className="p-8">Administrator access is required.</main>;
  return <div className="min-h-svh min-w-0 overflow-x-clip bg-muted/30">
    <header className="sticky top-0 z-30 border-b bg-background/95 backdrop-blur"><div className="mx-auto flex min-h-14 max-w-7xl flex-wrap items-center gap-y-2 px-3 py-2 sm:h-14 sm:flex-nowrap sm:px-5 sm:py-0">
      <Link href="/admin" className="whitespace-nowrap font-semibold">Data Lab Admin</Link>
      <nav className="order-3 flex w-full gap-1 overflow-x-auto pb-0.5 scrollbar-thin sm:order-none sm:ml-8 sm:w-auto sm:pb-0" aria-label="Admin">
        {links.map(([label, href, Icon]) => <Link key={href} href={href}
          className={cn("flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-sm",
            pathname === href ? "bg-accent font-medium" : "text-muted-foreground hover:text-foreground")}>
          <Icon className="size-4" />{label}</Link>)}
      </nav><div className="flex-1" />
      <Button variant="ghost" size="sm" className="shrink-0" onClick={() => logout()}><LogOut /><span className="hidden min-[380px]:inline">Log out</span></Button>
    </div></header>
    <main className="mx-auto min-w-0 max-w-7xl p-3 min-[380px]:p-4 sm:p-6">{children}</main>
  </div>;
}
