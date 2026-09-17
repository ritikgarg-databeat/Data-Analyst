"use client";

import { useState } from "react";
import { Crosshair, Star, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { TARGET_ROLE_CATEGORY_LABELS } from "@/features/career/constants";
import {
  useCareerProfile,
  useCreateTargetRole,
  useDeleteTargetRole,
  useRoleTemplates,
  useTargetRoles,
  useUpdateCareerProfile,
} from "@/features/career/use-career";

export function TargetRolesPage() {
  const profileQuery = useCareerProfile();
  const templatesQuery = useRoleTemplates();
  const targetRolesQuery = useTargetRoles();
  const createTargetRole = useCreateTargetRole();
  const deleteTargetRole = useDeleteTargetRole();
  const updateProfile = useUpdateCareerProfile();

  const [customTitle, setCustomTitle] = useState("");
  const [customNotes, setCustomNotes] = useState("");

  const isLoading = templatesQuery.isLoading || targetRolesQuery.isLoading;
  const isError = templatesQuery.isError || targetRolesQuery.isError;

  if (isLoading) return <LoadingState count={4} itemClassName="h-24" />;
  if (isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load target roles."
        retry={() => {
          void templatesQuery.refetch();
          void targetRolesQuery.refetch();
        }}
      />
    );
  }

  const primaryTargetRoleId = profileQuery.data?.primary_target_role_id ?? null;
  const targetRoles = targetRolesQuery.data ?? [];
  const templates = templatesQuery.data ?? [];

  function addCustomRole() {
    if (!customTitle.trim()) return;
    createTargetRole.mutate(
      { custom_title: customTitle.trim(), notes: customNotes.trim() || null },
      {
        onSuccess: () => {
          setCustomTitle("");
          setCustomNotes("");
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Your Target Roles</CardTitle>
        </CardHeader>
        <CardContent>
          {targetRoles.length === 0 ? (
            <EmptyState
              icon={Crosshair}
              title="No target roles yet"
              description="Add a role from a template below, or add a custom title of your own."
            />
          ) : (
            <ul className="flex flex-col gap-2">
              {targetRoles.map((role) => {
                const title = role.custom_title ?? role.role_template?.title ?? "Untitled role";
                const isPrimary = role.id === primaryTargetRoleId;
                return (
                  <li
                    key={role.id}
                    className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">{title}</p>
                        {isPrimary ? (
                          <Badge>
                            <Star className="size-3" aria-hidden="true" />
                            Primary
                          </Badge>
                        ) : null}
                        {role.role_template ? (
                          <Badge variant="outline">{TARGET_ROLE_CATEGORY_LABELS[role.role_template.category]}</Badge>
                        ) : null}
                      </div>
                      {role.notes ? <p className="mt-1 text-sm text-muted-foreground">{role.notes}</p> : null}
                    </div>
                    <div className="flex shrink-0 gap-2">
                      {!isPrimary ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateProfile.mutate({ primary_target_role_id: role.id })}
                          disabled={updateProfile.isPending}
                        >
                          Set Primary
                        </Button>
                      ) : null}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => deleteTargetRole.mutate(role.id)}
                        disabled={deleteTargetRole.isPending}
                        aria-label={`Delete ${title}`}
                      >
                        <Trash2 className="size-3.5" aria-hidden="true" />
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add a Custom Target Role</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Input
            value={customTitle}
            onChange={(event) => setCustomTitle(event.target.value)}
            placeholder="e.g. Senior Data Analyst, Growth Team"
            aria-label="Custom target role title"
          />
          <Textarea
            value={customNotes}
            onChange={(event) => setCustomNotes(event.target.value)}
            placeholder="Notes (optional)"
            rows={2}
            aria-label="Custom target role notes"
          />
          <Button
            className="self-start"
            onClick={addCustomRole}
            disabled={createTargetRole.isPending || !customTitle.trim()}
          >
            Add Custom Role
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Browse Role Templates</CardTitle>
        </CardHeader>
        <CardContent>
          {templates.length === 0 ? (
            <EmptyState icon={Crosshair} title="No role templates" description="No role templates are available yet." />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <div key={template.id} className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
                  <Badge variant="outline" className="w-fit">
                    {TARGET_ROLE_CATEGORY_LABELS[template.category]}
                  </Badge>
                  <p className="font-medium text-foreground">{template.title}</p>
                  {template.description ? (
                    <p className="text-sm text-muted-foreground">{template.description}</p>
                  ) : null}
                  <p className="text-xs text-muted-foreground">
                    Core skills: {template.core_skills.slice(0, 4).join(", ") || "—"}
                    {template.core_skills.length > 4 ? "…" : ""}
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-auto self-start"
                    onClick={() => createTargetRole.mutate({ role_template_slug: template.slug })}
                    disabled={createTargetRole.isPending}
                  >
                    Add as Target Role
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
