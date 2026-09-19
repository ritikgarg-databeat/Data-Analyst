"use client";

import type { AdminDashboardSummary } from "@data-analyst-lab/shared";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

export default function AdminDashboardPage() {
  const { data, isLoading, error } = useQuery({ queryKey:["admin","dashboard"], queryFn:()=>apiClient.get<AdminDashboardSummary>("/admin/dashboard") });
  if (isLoading) return <p>Loading dashboard…</p>; if (error || !data) return <p role="alert">Unable to load the administrator dashboard.</p>;
  const cards = [["Users",data.users],["Active",data.active_users],["Suspended",data.suspended_users],["Locked",data.locked_users],["New today",data.signups_today],["AI requests today",data.ai_requests_today]];
  return <div className="space-y-5"><div><h1 className="text-2xl font-semibold">Dashboard</h1><p className="text-muted-foreground">Account and AI usage overview</p></div>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{cards.map(([label,value])=><Card key={label}><CardHeader><CardTitle>{label}</CardTitle></CardHeader><CardContent className="text-3xl font-semibold">{value}</CardContent></Card>)}</div></div>;
}
