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
  return <div className="min-h-svh bg-muted/30">
    <header className="border-b bg-background"><div className="mx-auto flex h-14 max-w-7xl items-center px-5">
      <Link href="/admin" className="font-semibold">Data Lab Admin</Link>
      <nav className="ml-8 flex gap-1" aria-label="Admin">
        {links.map(([label, href, Icon]) => <Link key={href} href={href}
          className={cn("flex items-center gap-2 rounded-md px-3 py-2 text-sm",
            pathname === href ? "bg-accent font-medium" : "text-muted-foreground hover:text-foreground")}>
          <Icon className="size-4" />{label}</Link>)}
      </nav><div className="flex-1" />
      <Button variant="ghost" size="sm" onClick={() => logout()}><LogOut />Log out</Button>
    </div></header>
    <main className="mx-auto max-w-7xl p-6">{children}</main>
  </div>;
}
