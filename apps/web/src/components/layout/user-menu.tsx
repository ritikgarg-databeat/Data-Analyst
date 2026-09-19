"use client";

import Link from "next/link";
import { LogOut, Settings, ShieldCheck, UserRound, WifiOff } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCurrentUser } from "@/features/users/use-current-user";
import { useAuth } from "@/features/auth/auth-provider";

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0]}${parts[parts.length - 1]![0]}`.toUpperCase();
}

/** Top-bar user avatar + profile menu. Falls back gracefully when the API is unreachable. */
export function UserMenu() {
  const { data: user, isError } = useCurrentUser();
  const { logout } = useAuth();
  const displayName = user?.name ?? "Guest analyst";
  const initials = user ? getInitials(user.name) : "?";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="gap-2 px-2" aria-label="Open user menu">
          <Avatar className="size-7">
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
          <span className="hidden max-w-32 truncate text-sm font-medium sm:inline">{displayName}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex flex-col gap-0.5">
          <span className="font-medium text-foreground">{displayName}</span>
          {!user && (
            <span className="truncate text-xs font-normal text-muted-foreground">
              Not connected to the API
            </span>
          )}
          {user?.email ? (
            <span className="truncate text-xs font-normal text-muted-foreground">{user.email}</span>
          ) : null}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {isError ? (
          <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-muted-foreground">
            <WifiOff className="size-3.5" aria-hidden="true" />
            API unreachable — showing offline defaults
          </div>
        ) : null}
        <DropdownMenuItem asChild>
          <Link href="/settings">
            <Settings className="size-4" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/profile">
          <UserRound className="size-4" />
          Profile
          </Link>
        </DropdownMenuItem>
        {user?.role === "ADMIN" ? <DropdownMenuItem asChild><Link href="/admin"><ShieldCheck className="size-4" />Admin portal</Link></DropdownMenuItem> : null}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => logout()}><LogOut className="size-4" />Log out</DropdownMenuItem>
        <DropdownMenuItem onSelect={() => logout(true)}><LogOut className="size-4" />Log out all devices</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
