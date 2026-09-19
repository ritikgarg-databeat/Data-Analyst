"use client";

import type { AdminAuditEntry, PaginatedResponse } from "@data-analyst-lab/shared";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api-client";

export default function AdminAuditPage() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["admin", "audit", action, page],
    queryFn: () => apiClient.get<PaginatedResponse<AdminAuditEntry>>(`/admin/audit?page=${page}&action=${encodeURIComponent(action)}`),
  });
  const pages = Math.max(1, Math.ceil((query.data?.total ?? 0) / 50));
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-semibold">Audit</h1><p className="text-muted-foreground">Security-sensitive administrator actions</p></div>
      <div className="max-w-sm"><Label htmlFor="audit-search">Action contains</Label><Input id="audit-search" placeholder="user.password_reset" value={action} onChange={(event) => { setAction(event.target.value); setPage(1); }} /></div>
      <div className="rounded-lg border bg-background">
        {query.isLoading ? <p className="p-4">Loading…</p> : query.error ? <p role="alert" className="p-4 text-destructive">Unable to load audit history.</p> : query.data?.items.length ? query.data.items.map((row) => (
          <div className="border-b p-4 last:border-0" key={row.id}>
            <div className="flex flex-wrap justify-between gap-2"><strong>{row.action}</strong><time className="text-sm text-muted-foreground">{new Date(row.created_at).toLocaleString()}</time></div>
            <p className="text-xs text-muted-foreground">Actor {row.actor_user_id ?? "deleted"} · Target {row.target_user_id ?? "none"}</p>
            {row.details ? <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(row.details, null, 2)}</pre> : null}
          </div>
        )) : <p className="p-6 text-muted-foreground">No audit events found.</p>}
      </div>
      <div className="flex justify-end gap-2"><Button variant="outline" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</Button><Button variant="outline" disabled={page >= pages} onClick={() => setPage((value) => value + 1)}>Next</Button></div>
    </div>
  );
}
