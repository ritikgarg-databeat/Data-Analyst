"use client";

import type { AuthResponse, AuthUserProfile } from "@data-analyst-lab/shared";
import { useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef } from "react";

import { currentUserQueryKey, useCurrentUser } from "@/features/users/use-current-user";
import { apiClient, ApiError } from "@/lib/api-client";

interface AuthContextValue {
  user: AuthUserProfile | undefined;
  loading: boolean;
  setAuthenticatedUser: (response: AuthResponse) => void;
  logout: (all?: boolean) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const PUBLIC_PATHS = new Set(["/", "/login", "/signup", "/forgot-password", "/admin/login"]);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  // The landing page is fully public and static; do not make it wait for an
  // account request or a refresh-token round trip before it can render.
  const query = useCurrentUser(pathname !== "/");
  const previousUserId = useRef<string | undefined>(undefined);

  useEffect(() => {
    const currentId = query.data?.id;
    if (previousUserId.current && currentId && previousUserId.current !== currentId) {
      queryClient.clear();
    }
    previousUserId.current = currentId;
  }, [query.data?.id, queryClient]);

  useEffect(() => {
    if (query.isLoading) return;
    const unauthenticated = query.error instanceof ApiError && [401, 403].includes(query.error.status);
    if (unauthenticated && !PUBLIC_PATHS.has(pathname)) {
      router.replace(pathname.startsWith("/admin") ? "/admin/login" : "/login");
      return;
    }
    if (query.data?.must_change_password && pathname !== "/change-password") {
      router.replace("/change-password");
      return;
    }
    if (query.data && pathname.startsWith("/admin") && pathname !== "/admin/login" && query.data.role !== "ADMIN") {
      router.replace("/dashboard");
      return;
    }
    if (query.data && pathname === "/admin/login" && query.data.role === "ADMIN") router.replace("/admin");
    if (query.data && (pathname === "/login" || pathname === "/signup")) router.replace("/dashboard");
  }, [pathname, query.data, query.error, query.isLoading, router]);

  const setAuthenticatedUser = useCallback((response: AuthResponse) => {
    queryClient.clear();
    queryClient.setQueryData(currentUserQueryKey, response.user);
    previousUserId.current = response.user.id;
  }, [queryClient]);

  const logout = useCallback(async (all = false) => {
    try {
      await apiClient.post(all ? "/auth/logout-all" : "/auth/logout");
    } finally {
      previousUserId.current = undefined;
      queryClient.clear();
      router.replace("/login");
    }
  }, [queryClient, router]);

  const value = useMemo(() => ({ user: query.data, loading: pathname !== "/" && query.isLoading,
    setAuthenticatedUser, logout }), [logout, pathname, query.data, query.isLoading, setAuthenticatedUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
