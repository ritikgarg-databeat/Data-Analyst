"use client";

import type { AdminDataRow, AdminUserDetail, PaginatedResponse, UserRole } from "@data-analyst-lab/shared";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { API_BASE_URL, apiClient } from "@/lib/api-client";

const sections = ["learning", "labs", "projects", "datasets", "career", "interviews", "ai"] as const;

function UserDetail({ user }: { user: AdminUserDetail }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user: actor } = useAuth();
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [quota, setQuota] = useState(user.ai_daily_quota);
  const [adminPassword, setAdminPassword] = useState("");
  const [temporary, setTemporary] = useState("");
  const [confirmationEmail, setConfirmationEmail] = useState("");
  const [section, setSection] = useState<(typeof sections)[number]>("learning");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const isSelf = actor?.id === user.id;

  const dataQuery = useQuery({
    queryKey: ["admin", "users", user.id, "data", section],
    queryFn: () => apiClient.get<PaginatedResponse<AdminDataRow>>(`/admin/users/${user.id}/data/${section}`),
  });

  const refresh = async (notice: string) => {
    setError("");
    setMessage(notice);
    await queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
  };

  const accountAction = useMutation({
    mutationFn: (path: string) => apiClient.post(`/admin/users/${user.id}/${path}`),
    onSuccess: (_result, path) => refresh(path === "revoke-sessions" ? "Sessions revoked." : "Account updated."),
    onError: (reason: Error) => setError(reason.message),
  });

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    try {
      await apiClient.patch(`/admin/users/${user.id}`, {
        name,
        email,
        current_password: email === user.email ? undefined : adminPassword,
      });
      setAdminPassword("");
      await refresh("Profile updated.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Profile update failed.");
    }
  }

  async function resetPassword() {
    try {
      const result = await apiClient.post<{ temporary_password: string }>(
        `/admin/users/${user.id}/reset-password`,
        { current_password: adminPassword },
      );
      setTemporary(result.temporary_password);
      setAdminPassword("");
      await refresh("Temporary password generated. Copy it now; it will not be shown again.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Password reset failed.");
    }
  }

  async function saveAI() {
    try {
      await apiClient.put(`/admin/users/${user.id}/ai`, {
        enabled: !user.ai_grant_enabled,
        daily_quota: quota,
      });
      await refresh(user.ai_grant_enabled ? "AI access disabled." : "AI access enabled.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "AI update failed.");
    }
  }

  async function changeRole(role: UserRole) {
    try {
      await apiClient.put(`/admin/users/${user.id}/role`, {
        role,
        current_password: adminPassword,
      });
      setAdminPassword("");
      await refresh("Role updated and user sessions revoked.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Role update failed.");
    }
  }

  async function deleteUser() {
    if (!window.confirm(`Permanently delete ${user.email} and all private data?`)) return;
    try {
      await apiClient.delete(`/admin/users/${user.id}`, {
        body: { confirmation_email: confirmationEmail, current_password: adminPassword },
      });
      router.replace("/admin/users");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Deletion failed.");
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">{user.name}</h1>
        <p className="text-muted-foreground">{user.email} · {user.role} · {user.status}</p>
      </div>
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
      {message ? <p role="status" className="text-sm text-emerald-700">{message}</p> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Profile and account</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <form className="space-y-3" onSubmit={saveProfile}>
              <div><Label htmlFor="user-name">Name</Label><Input id="user-name" value={name} onChange={(event) => setName(event.target.value)} required /></div>
              <div><Label htmlFor="user-email">Email</Label><Input id="user-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></div>
              <Button type="submit">Save profile</Button>
            </form>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" disabled={isSelf} onClick={() => accountAction.mutate(user.status === "ACTIVE" ? "suspend" : "reactivate")}>{user.status === "ACTIVE" ? "Suspend" : "Reactivate"}</Button>
              <Button variant="outline" onClick={() => accountAction.mutate("unlock")}>Unlock</Button>
              <Button variant="outline" onClick={() => accountAction.mutate("revoke-sessions")}>Revoke sessions</Button>
            </div>
            <p className="text-xs text-muted-foreground">Failed attempts: {user.failed_login_count}. {user.locked_until ? `Locked until ${new Date(user.locked_until).toLocaleString()}.` : "Not locked."}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>AI entitlement</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">Grant: {user.ai_grant_enabled ? "enabled" : "disabled"}; preference: {user.ai_preference_enabled ? "on" : "off"}; effective access: {user.effective_ai_access_enabled ? "on" : "off"}.</p>
            <Label htmlFor="quota">Daily quota (maximum 200)</Label>
            <Input id="quota" type="number" min={1} max={200} value={quota} onChange={(event) => setQuota(Number(event.target.value))} />
            <Button onClick={saveAI}>{user.ai_grant_enabled ? "Disable AI" : "Enable AI"}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Security actions</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div><Label htmlFor="admin-password">Your administrator password</Label><Input id="admin-password" type="password" autoComplete="current-password" value={adminPassword} onChange={(event) => setAdminPassword(event.target.value)} /></div>
            <div className="flex flex-wrap gap-2">
              <Button variant="destructive" onClick={resetPassword}>Reset password</Button>
              <Button variant="outline" disabled={isSelf} onClick={() => changeRole(user.role === "ADMIN" ? "USER" : "ADMIN")}>{user.role === "ADMIN" ? "Demote to user" : "Promote to admin"}</Button>
            </div>
            {temporary ? <div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Shown once · expires in 24 hours</p><code className="break-all">{temporary}</code></div> : null}
          </CardContent>
        </Card>

        <Card className="border-destructive/40">
          <CardHeader><CardTitle>Permanent deletion</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">Enter the target email and your administrator password above. This removes database records, private files, and active runtimes.</p>
            <Label htmlFor="confirm-email">Confirmation email</Label>
            <Input id="confirm-email" type="email" value={confirmationEmail} onChange={(event) => setConfirmationEmail(event.target.value)} />
            <Button variant="destructive" disabled={isSelf || confirmationEmail !== user.email || !adminPassword} onClick={deleteUser}>Delete user permanently</Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Read-only user data</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2" role="tablist" aria-label="User data section">
            {sections.map((item) => <Button role="tab" aria-selected={section === item} variant={section === item ? "default" : "outline"} key={item} onClick={() => setSection(item)}>{item}</Button>)}
          </div>
          {dataQuery.isLoading ? <p>Loading {section} data…</p> : dataQuery.error ? <p role="alert">Unable to load this section.</p> : dataQuery.data?.items.length ? (
            <div className="space-y-2">
              {dataQuery.data.items.map((row, index) => (
                <details className="rounded-md border p-3" key={`${row.type}-${String(row.data.id ?? index)}`}>
                  <summary className="cursor-pointer font-medium">{row.type}</summary>
                  <pre className="mt-3 overflow-auto text-xs">{JSON.stringify(row.data, null, 2)}</pre>
                  {section === "datasets" && row.type === "datasets" && row.data.id ? <a className="mt-2 inline-block text-sm underline" href={`${API_BASE_URL}/api/v1/admin/users/${user.id}/datasets/${String(row.data.id)}/download`}>Download private file</a> : null}
                </details>
              ))}
            </div>
          ) : <p className="text-sm text-muted-foreground">No {section} records.</p>}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AdminUserDetailPage() {
  const id = String(useParams().id);
  const query = useQuery({
    queryKey: ["admin", "users", id],
    queryFn: () => apiClient.get<AdminUserDetail>(`/admin/users/${id}`),
  });
  if (query.isLoading) return <p>Loading user…</p>;
  if (query.error || !query.data) return <p role="alert">Unable to load this user.</p>;
  return <UserDetail user={query.data} />;
}
