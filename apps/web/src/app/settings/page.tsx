"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { API_BASE_URL } from "@/lib/api-client";
import { useCurrentUser } from "@/features/users/use-current-user";
import { useUpdateUser } from "@/features/users/use-update-user";

import { AISettingsCard } from "./ai-settings-card";
import { BackupRestoreCard } from "./backup-restore-card";
import { SystemHealthCard } from "./system-health-card";
import { ThemePreferenceCard } from "./theme-preference-card";

const profileSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Display name is required")
    .max(100, "Display name must be 100 characters or fewer"),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const APP_VERSION = "0.1.0";

function ProfileForm() {
  const { data: user, isLoading, isError, refetch } = useCurrentUser();
  const updateUser = useUpdateUser();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isSubmitSuccessful },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: "" },
  });

  React.useEffect(() => {
    if (user) reset({ name: user.name });
  }, [user, reset]);

  const onSubmit = handleSubmit((values) => {
    updateUser.mutate(
      { name: values.name },
      {
        onSuccess: (updated) => reset({ name: updated.name }),
      },
    );
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-9 w-full max-w-sm" />
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load your profile"
        message="We couldn't reach the API to load your profile. You can still adjust local preferences below."
        retry={() => void refetch()}
      />
    );
  }

  return (
    <form onSubmit={onSubmit} className="flex max-w-sm flex-col gap-4" noValidate>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="display-name">Display name</Label>
        <Input id="display-name" aria-invalid={Boolean(errors.name)} {...register("name")} />
        {errors.name ? (
          <p className="text-xs text-destructive" role="alert">
            {errors.name.message}
          </p>
        ) : null}
      </div>
      <div className="flex items-center gap-3">
        <Button type="submit" size="sm" disabled={!isDirty || updateUser.isPending}>
          {updateUser.isPending ? "Saving…" : "Save changes"}
        </Button>
        {isSubmitSuccessful && !isDirty && !updateUser.isPending ? (
          <span className="text-xs text-success" role="status">
            Saved
          </span>
        ) : null}
        {updateUser.isError ? (
          <span className="text-xs text-destructive" role="alert">
            Couldn&apos;t save — is the API running?
          </span>
        ) : null}
      </div>
    </form>
  );
}

export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Settings" subtitle="Manage your profile, preferences, environment, and data." />

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="ai">AI</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="flex flex-col gap-6">
          <Card className="max-w-2xl">
            <CardHeader>
              <CardTitle>Profile</CardTitle>
              <CardDescription>Your display name, stored locally via the API.</CardDescription>
            </CardHeader>
            <CardContent>
              <ProfileForm />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="flex flex-col gap-6">
          <ThemePreferenceCard />
        </TabsContent>

        <TabsContent value="ai" className="flex flex-col gap-6">
          <AISettingsCard />
        </TabsContent>

        <TabsContent value="system" className="flex flex-col gap-6">
          <SystemHealthCard />
          <Card className="max-w-2xl">
            <CardHeader>
              <CardTitle>Environment</CardTitle>
              <CardDescription>Read-only information about this local installation.</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">App version</dt>
                  <dd className="text-sm text-foreground">{APP_VERSION}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">API URL</dt>
                  <dd className="text-sm break-all text-foreground">
                    {API_BASE_URL || "Same origin (/api/v1)"}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data" className="flex flex-col gap-6">
          <BackupRestoreCard />
        </TabsContent>
      </Tabs>
    </div>
  );
}
