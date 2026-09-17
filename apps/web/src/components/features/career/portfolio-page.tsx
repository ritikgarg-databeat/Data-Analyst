"use client";

import { useState } from "react";
import Link from "next/link";
import { LayoutGrid, Sparkles, Trash2 } from "lucide-react";
import type { PortfolioItemType, PrivacyLevel } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import {
  PORTFOLIO_ITEM_TYPE_LABELS,
  PORTFOLIO_ITEM_TYPE_ORDER,
  PRIVACY_LEVEL_LABELS,
  PRIVACY_LEVEL_ORDER,
} from "@/features/career/constants";
import { useTargetRoles } from "@/features/career/use-career";
import {
  useCreatePortfolioItem,
  useDeletePortfolioItem,
  usePortfolio,
  usePortfolioGaps,
  usePortfolioQualityScore,
  useReviewPortfolio,
  useUpdatePortfolio,
  useUpdatePortfolioItem,
} from "@/features/career/use-portfolio";

export function PortfolioPage() {
  const portfolioQuery = usePortfolio();
  const qualityScoreQuery = usePortfolioQualityScore();
  const targetRolesQuery = useTargetRoles();
  const updatePortfolio = useUpdatePortfolio();
  const createItem = useCreatePortfolioItem();
  const updateItem = useUpdatePortfolioItem();
  const deleteItem = useDeletePortfolioItem();
  const reviewPortfolio = useReviewPortfolio();

  const [editingProfile, setEditingProfile] = useState(false);
  const [headline, setHeadline] = useState("");
  const [about, setAbout] = useState("");
  const [itemType, setItemType] = useState<PortfolioItemType>("PROJECT");
  const [itemRefId, setItemRefId] = useState("");
  const [itemTitle, setItemTitle] = useState("");
  const [itemDescription, setItemDescription] = useState("");
  const [itemPrivacy, setItemPrivacy] = useState<PrivacyLevel>("PRIVATE");
  const [gapTargetRoleId, setGapTargetRoleId] = useState("");

  const gapsQuery = usePortfolioGaps(gapTargetRoleId || undefined);

  if (portfolioQuery.isLoading) return <LoadingState count={4} itemClassName="h-24" />;
  if (portfolioQuery.isError || !portfolioQuery.data) {
    return <ErrorState message="We couldn't reach the API to load your portfolio." retry={() => void portfolioQuery.refetch()} />;
  }

  const portfolio = portfolioQuery.data;

  function startEditingProfile() {
    setHeadline(portfolio.headline ?? "");
    setAbout(portfolio.about ?? "");
    setEditingProfile(true);
  }

  function saveProfile() {
    updatePortfolio.mutate({ headline, about }, { onSuccess: () => setEditingProfile(false) });
  }

  function handleAddItem() {
    if (!itemTitle.trim()) return;
    createItem.mutate(
      {
        item_type: itemType,
        ref_id: itemRefId.trim() || null,
        title: itemTitle.trim(),
        description: itemDescription.trim() || null,
        privacy: itemPrivacy,
      },
      {
        onSuccess: () => {
          setItemRefId("");
          setItemTitle("");
          setItemDescription("");
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Portfolio Profile</CardTitle>
            {!editingProfile ? (
              <Button size="sm" variant="outline" onClick={startEditingProfile}>
                Edit
              </Button>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {editingProfile ? (
            <>
              <Input value={headline} onChange={(event) => setHeadline(event.target.value)} placeholder="Headline" aria-label="Portfolio headline" />
              <Textarea value={about} onChange={(event) => setAbout(event.target.value)} placeholder="About" rows={3} aria-label="Portfolio about" />
              <div className="flex gap-2">
                <Button size="sm" onClick={saveProfile} disabled={updatePortfolio.isPending}>
                  Save
                </Button>
                <Button size="sm" variant="outline" onClick={() => setEditingProfile(false)}>
                  Cancel
                </Button>
              </div>
            </>
          ) : (
            <>
              <p className="font-medium text-foreground">{portfolio.headline || "No headline yet"}</p>
              <p className="text-sm text-muted-foreground">{portfolio.about || "Add an about section."}</p>
            </>
          )}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={portfolio.is_public_ready}
              onChange={(event) => updatePortfolio.mutate({ is_public_ready: event.target.checked })}
            />
            <span className="text-foreground">Public ready</span>
            <span className="text-xs text-muted-foreground">(items still default to Private individually)</span>
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quality Score</CardTitle>
        </CardHeader>
        <CardContent>
          {qualityScoreQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-16" />
          ) : qualityScoreQuery.isError || !qualityScoreQuery.data ? (
            <p className="text-sm text-muted-foreground">Couldn&apos;t load quality score.</p>
          ) : (
            <>
              <p className="text-2xl font-semibold text-foreground">{qualityScoreQuery.data.score.toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">
                {qualityScoreQuery.data.item_count} item{qualityScoreQuery.data.item_count === 1 ? "" : "s"} ·{" "}
                {qualityScoreQuery.data.items_with_description} with a description ·{" "}
                {qualityScoreQuery.data.portfolio_ready_item_count} public-ready
              </p>
              {qualityScoreQuery.data.suggestions.length > 0 ? (
                <ul className="mt-2 list-inside list-disc text-xs text-muted-foreground">
                  {qualityScoreQuery.data.suggestions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </>
          )}
          <Button size="sm" variant="outline" className="mt-3" onClick={() => reviewPortfolio.mutate()} disabled={reviewPortfolio.isPending}>
            <Sparkles className="size-4" aria-hidden="true" />
            {reviewPortfolio.isPending ? "Reviewing..." : "AI Review"}
          </Button>
          {reviewPortfolio.data ? (
            <p className="mt-2 rounded-md border border-border bg-muted/40 p-2 text-xs whitespace-pre-wrap text-foreground">
              {reviewPortfolio.data.raw_text}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Portfolio Items</CardTitle>
        </CardHeader>
        <CardContent>
          {portfolio.items.length === 0 ? (
            <EmptyState icon={LayoutGrid} title="No portfolio items yet" description="Add a project, case study, certification, or skill highlight below." />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {portfolio.items
                .slice()
                .sort((a, b) => a.display_order - b.display_order)
                .map((item) => (
                  <div key={item.id} className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Badge variant="outline">{PORTFOLIO_ITEM_TYPE_LABELS[item.item_type]}</Badge>
                    </div>
                    <p className="font-medium text-foreground">{item.title}</p>
                    {item.description ? <p className="text-sm text-muted-foreground">{item.description}</p> : null}
                    <div className="mt-auto flex items-center justify-between gap-2 pt-1">
                      <Select
                        value={item.privacy}
                        onChange={(event) => updateItem.mutate({ id: item.id, privacy: event.target.value as PrivacyLevel })}
                        className="h-8 w-36 text-xs"
                        aria-label={`Privacy for ${item.title}`}
                      >
                        {PRIVACY_LEVEL_ORDER.map((level) => (
                          <option key={level} value={level}>
                            {PRIVACY_LEVEL_LABELS[level]}
                          </option>
                        ))}
                      </Select>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => deleteItem.mutate(item.id)}
                        disabled={deleteItem.isPending}
                        aria-label={`Delete ${item.title}`}
                      >
                        <Trash2 className="size-3.5" aria-hidden="true" />
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add a Portfolio Item</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Select value={itemType} onChange={(event) => setItemType(event.target.value as PortfolioItemType)} aria-label="Item type">
              {PORTFOLIO_ITEM_TYPE_ORDER.map((type) => (
                <option key={type} value={type}>
                  {PORTFOLIO_ITEM_TYPE_LABELS[type]}
                </option>
              ))}
            </Select>
            <Input value={itemRefId} onChange={(event) => setItemRefId(event.target.value)} placeholder="Ref ID (optional, e.g. project ID)" aria-label="Reference ID" />
            <Select
              value={itemPrivacy}
              onChange={(event) => setItemPrivacy(event.target.value as PrivacyLevel)}
              aria-label="Privacy"
            >
              {PRIVACY_LEVEL_ORDER.map((level) => (
                <option key={level} value={level}>
                  {PRIVACY_LEVEL_LABELS[level]}
                </option>
              ))}
            </Select>
          </div>
          <p className="text-xs text-muted-foreground">Privacy defaults to Private if you don&apos;t change it — nothing here is public until you choose to make it so.</p>
          <Input value={itemTitle} onChange={(event) => setItemTitle(event.target.value)} placeholder="Title" aria-label="Item title" />
          <Textarea value={itemDescription} onChange={(event) => setItemDescription(event.target.value)} placeholder="Description (optional)" rows={2} aria-label="Item description" />
          <Button className="self-start" onClick={handleAddItem} disabled={createItem.isPending || !itemTitle.trim()}>
            Add Item
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Portfolio Gap Detection</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Select value={gapTargetRoleId} onChange={(event) => setGapTargetRoleId(event.target.value)} className="w-64" aria-label="Target role for portfolio gaps">
            <option value="">Choose a target role (optional)...</option>
            {(targetRolesQuery.data ?? []).map((role) => (
              <option key={role.id} value={role.id}>
                {role.custom_title ?? role.role_template?.title ?? "Untitled role"}
              </option>
            ))}
          </Select>
          {gapsQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-16" />
          ) : gapsQuery.isError || !gapsQuery.data ? (
            <p className="text-sm text-muted-foreground">Couldn&apos;t load portfolio gaps.</p>
          ) : gapsQuery.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No missing skills found for your portfolio.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {gapsQuery.data.map((gap) => (
                <li key={gap.skill_slug} className="rounded-md border border-border bg-card p-2 text-sm">
                  <p className="font-medium text-foreground">{gap.skill_slug}</p>
                  <div className="mt-1 flex flex-wrap gap-1.5 text-xs">
                    {gap.recommended_project_template_slugs.map((slug) => (
                      <Link key={slug} href="/projects" className="rounded-md border border-border px-2 py-1 text-primary hover:underline">
                        {slug}
                      </Link>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
