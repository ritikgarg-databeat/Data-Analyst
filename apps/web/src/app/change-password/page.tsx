"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AuthCard } from "@/components/features/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { apiClient } from "@/lib/api-client";

export default function ChangePasswordPage() {
  const router = useRouter(); const { user, logout } = useAuth();
  const [current, setCurrent] = useState(""); const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState(""); const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault();
    if (next !== confirm) { setError("New passwords do not match."); return; }
    setBusy(true); setError(""); try { await apiClient.post("/auth/change-password", { current_password: current, new_password: next }); await logout(); router.replace("/login"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Password change failed."); } finally { setBusy(false); } }
  return <AuthCard title={user?.must_change_password ? "Replace temporary password" : "Change password"}
    description="Changing your password signs out every active session.">
    <form className="space-y-4" onSubmit={submit}>
      <div className="space-y-2"><Label htmlFor="current">Current password</Label><Input id="current" type="password" autoComplete="current-password" required value={current} onChange={e=>setCurrent(e.target.value)} /></div>
      <div className="space-y-2"><Label htmlFor="next">New password</Label><Input id="next" type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={next} onChange={e=>setNext(e.target.value)} /></div>
      <div className="space-y-2"><Label htmlFor="confirm">Confirm new password</Label><Input id="confirm" type="password" autoComplete="new-password" required value={confirm} onChange={e=>setConfirm(e.target.value)} /></div>
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}<Button className="w-full" disabled={busy}>{busy ? "Changing…" : "Change password"}</Button>
    </form>
  </AuthCard>;
}
