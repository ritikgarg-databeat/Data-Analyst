"use client";

import { usePathname } from "next/navigation";
import dynamic from "next/dynamic";

import { useAuth } from "@/features/auth/auth-provider";

const AdminShell = dynamic(() => import("./admin-shell").then(module => module.AdminShell));
const AppShell = dynamic(() => import("./app-shell").then(module => module.AppShell));

const BARE_PATHS = new Set(["/", "/login", "/signup", "/forgot-password", "/change-password", "/admin/login"]);

export function AppFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { loading } = useAuth();
  // Keep public/auth routes out of the large workspace shell bundle.
  if (BARE_PATHS.has(pathname)) return <>{children}</>;
  if (loading) return <main className="grid min-h-svh place-items-center text-sm text-muted-foreground">Loading account…</main>;
  if (pathname.startsWith("/admin")) return <AdminShell>{children}</AdminShell>;
  return <AppShell>{children}</AppShell>;
}
