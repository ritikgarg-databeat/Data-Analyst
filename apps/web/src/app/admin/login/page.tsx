"use client";

import type { AuthResponse } from "@data-analyst-lab/shared";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AuthCard } from "@/components/features/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { apiClient } from "@/lib/api-client";

export default function AdminLoginPage() {
  const router = useRouter(); const { setAuthenticatedUser } = useAuth();
  const [email,setEmail]=useState(""); const [password,setPassword]=useState("");
  const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  async function submit(event:FormEvent){event.preventDefault();setBusy(true);setError("");try{
    const result=await apiClient.post<AuthResponse>("/auth/admin/login",{email,password});setAuthenticatedUser(result);
    router.replace(result.user.must_change_password?"/change-password":"/admin");
  }catch(reason){setError(reason instanceof Error?reason.message:"Sign in failed.");}finally{setBusy(false);}}
  return <AuthCard title="Administrator sign in" description="Manage users, access, and shared content"
    footer={<Link className="text-primary underline" href="/login">Learner sign in</Link>}><form className="space-y-4" onSubmit={submit}>
    <div className="space-y-2"><Label htmlFor="email">Admin email</Label><Input id="email" type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)}/></div>
    <div className="space-y-2"><Label htmlFor="password">Password</Label><Input id="password" type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)}/></div>
    {error?<p role="alert" className="text-sm text-destructive">{error}</p>:null}<Button className="w-full" disabled={busy}>{busy?"Signing in…":"Sign in as administrator"}</Button>
  </form></AuthCard>;
}
