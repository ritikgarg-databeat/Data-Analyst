"use client";

import type { AdminUserSummary, PaginatedResponse } from "@data-analyst-lab/shared";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api-client";

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [ai, setAi] = useState("");
  const [page, setPage] = useState(1);
  const params = new URLSearchParams({ page: String(page), page_size: "25" });
  if (search) params.set("search", search);
  if (role) params.set("role", role);
  if (status) params.set("status", status);
  if (ai) params.set("ai_enabled", ai);
  const query = useQuery({
    queryKey: ["admin", "users", search, role, status, ai, page],
    queryFn: () => apiClient.get<PaginatedResponse<AdminUserSummary>>(`/admin/users?${params}`),
  });
  const totalPages = Math.max(1, Math.ceil((query.data?.total ?? 0) / 25));

  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-semibold">Users</h1><p className="text-muted-foreground">Search accounts and manage access</p></div>
      <div className="grid gap-3 md:grid-cols-4">
        <div><Label htmlFor="user-search">Search</Label><Input id="user-search" placeholder="Name or email" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} /></div>
        <div><Label htmlFor="role-filter">Role</Label><select id="role-filter" className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={role} onChange={(event) => { setRole(event.target.value); setPage(1); }}><option value="">All roles</option><option value="USER">User</option><option value="ADMIN">Admin</option></select></div>
        <div><Label htmlFor="status-filter">Status</Label><select id="status-filter" className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">All statuses</option><option value="ACTIVE">Active</option><option value="SUSPENDED">Suspended</option></select></div>
        <div><Label htmlFor="ai-filter">AI grant</Label><select id="ai-filter" className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={ai} onChange={(event) => { setAi(event.target.value); setPage(1); }}><option value="">All</option><option value="true">Enabled</option><option value="false">Disabled</option></select></div>
      </div>

      <div className="overflow-hidden rounded-lg border bg-background">
        <div className="hidden grid-cols-[1fr_1fr_auto_auto_auto] gap-4 border-b bg-muted/40 px-4 py-3 text-xs font-medium uppercase text-muted-foreground md:grid"><span>User</span><span>Email</span><span>Role</span><span>Status</span><span>AI</span></div>
        {query.isLoading ? <p className="p-4">Loading users…</p> : query.error ? <p role="alert" className="p-4 text-destructive">Unable to load users.</p> : query.data?.items.length ? query.data.items.map((user) => (
          <Link key={user.id} href={`/admin/users/${user.id}`} className="grid gap-2 border-b px-4 py-3 text-sm last:border-0 hover:bg-muted/30 md:grid-cols-[1fr_1fr_auto_auto_auto] md:gap-4">
            <span className="font-medium">{user.name}</span><span className="truncate text-muted-foreground">{user.email}</span><Badge variant="outline">{user.role}</Badge><Badge variant="outline">{user.is_locked ? "LOCKED" : user.status}</Badge><span>{user.ai_grant_enabled ? `${user.ai_requests_today}/${user.ai_daily_quota}` : "Off"}</span>
          </Link>
        )) : <p className="p-6 text-center text-muted-foreground">No users found.</p>}
      </div>
      <div className="flex items-center justify-between text-sm">
        <span>{query.data?.total ?? 0} users · Page {page} of {totalPages}</span>
        <div className="flex gap-2"><Button variant="outline" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</Button><Button variant="outline" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>Next</Button></div>
      </div>
    </div>
  );
}
