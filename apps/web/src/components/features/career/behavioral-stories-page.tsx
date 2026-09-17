"use client";

import { useMemo, useState } from "react";
import { BookMarked, CheckCircle2, Trash2 } from "lucide-react";
import type { BehavioralStory, BehavioralStoryCategory } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { BEHAVIORAL_STORY_CATEGORY_LABELS, BEHAVIORAL_STORY_CATEGORY_ORDER } from "@/features/career/constants";
import {
  useBehavioralStories,
  useBehavioralStoryCoverage,
  useCreateBehavioralStory,
  useDeleteBehavioralStory,
  usePracticeBehavioralStory,
  useUpdateBehavioralStory,
} from "@/features/career/use-career";

const EMPTY_FORM = { category: "OWNERSHIP" as BehavioralStoryCategory, title: "", situation: "", task: "", action: "", result: "" };

export function BehavioralStoriesPage() {
  const storiesQuery = useBehavioralStories();
  const coverageQuery = useBehavioralStoryCoverage();
  const createStory = useCreateBehavioralStory();
  const updateStory = useUpdateBehavioralStory();
  const deleteStory = useDeleteBehavioralStory();
  const practiceStory = usePracticeBehavioralStory();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const storiesByCategory = useMemo(() => {
    const map = new Map<BehavioralStoryCategory, BehavioralStory[]>();
    for (const category of BEHAVIORAL_STORY_CATEGORY_ORDER) map.set(category, []);
    for (const story of storiesQuery.data ?? []) {
      map.set(story.category, [...(map.get(story.category) ?? []), story]);
    }
    return map;
  }, [storiesQuery.data]);

  if (storiesQuery.isLoading) return <LoadingState count={4} itemClassName="h-24" />;
  if (storiesQuery.isError) {
    return <ErrorState message="We couldn't reach the API to load your behavioral stories." retry={() => void storiesQuery.refetch()} />;
  }

  function startEdit(story: BehavioralStory) {
    setEditingId(story.id);
    setForm({
      category: story.category,
      title: story.title,
      situation: story.situation,
      task: story.task,
      action: story.action,
      result: story.result,
    });
  }

  function resetForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  function handleSubmit() {
    if (!form.title.trim() || !form.situation.trim() || !form.task.trim() || !form.action.trim() || !form.result.trim()) return;
    if (editingId) {
      updateStory.mutate(
        { id: editingId, title: form.title, situation: form.situation, task: form.task, action: form.action, result: form.result },
        { onSuccess: resetForm },
      );
    } else {
      createStory.mutate(form, { onSuccess: resetForm });
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Coverage</CardTitle>
        </CardHeader>
        <CardContent>
          {coverageQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-16" />
          ) : coverageQuery.isError || !coverageQuery.data ? (
            <p className="text-sm text-muted-foreground">Couldn&apos;t load coverage.</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {coverageQuery.data.coverage.map((entry) => (
                <Badge key={entry.category} variant={entry.has_coverage ? "outline" : "destructive"}>
                  {BEHAVIORAL_STORY_CATEGORY_LABELS[entry.category]} ({entry.story_count})
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{editingId ? "Edit Story" : "Add a Story"}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Select
              value={form.category}
              onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value as BehavioralStoryCategory }))}
              disabled={Boolean(editingId)}
              aria-label="Category"
            >
              {BEHAVIORAL_STORY_CATEGORY_ORDER.map((category) => (
                <option key={category} value={category}>
                  {BEHAVIORAL_STORY_CATEGORY_LABELS[category]}
                </option>
              ))}
            </Select>
            <Input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} placeholder="Title" aria-label="Title" />
          </div>
          <Textarea value={form.situation} onChange={(event) => setForm((prev) => ({ ...prev, situation: event.target.value }))} placeholder="Situation" rows={2} aria-label="Situation" />
          <Textarea value={form.task} onChange={(event) => setForm((prev) => ({ ...prev, task: event.target.value }))} placeholder="Task" rows={2} aria-label="Task" />
          <Textarea value={form.action} onChange={(event) => setForm((prev) => ({ ...prev, action: event.target.value }))} placeholder="Action" rows={2} aria-label="Action" />
          <Textarea value={form.result} onChange={(event) => setForm((prev) => ({ ...prev, result: event.target.value }))} placeholder="Result" rows={2} aria-label="Result" />
          <div className="flex gap-2">
            <Button onClick={handleSubmit} disabled={createStory.isPending || updateStory.isPending}>
              {editingId ? "Save Changes" : "Add Story"}
            </Button>
            {editingId ? (
              <Button variant="outline" onClick={resetForm}>
                Cancel
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {BEHAVIORAL_STORY_CATEGORY_ORDER.map((category) => {
        const stories = storiesByCategory.get(category) ?? [];
        if (stories.length === 0) return null;
        return (
          <Card key={category}>
            <CardHeader>
              <CardTitle>{BEHAVIORAL_STORY_CATEGORY_LABELS[category]}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-3">
                {stories.map((story) => (
                  <li key={story.id} className="rounded-xl border border-border bg-card p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium text-foreground">{story.title}</p>
                      <div className="flex shrink-0 items-center gap-2">
                        {story.last_practiced_at ? (
                          <Badge variant="outline">
                            <CheckCircle2 className="size-3" aria-hidden="true" />
                            Practiced
                          </Badge>
                        ) : null}
                        <Button size="sm" variant="outline" onClick={() => practiceStory.mutate(story.id)} disabled={practiceStory.isPending}>
                          Mark Practiced
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => startEdit(story)}>
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteStory.mutate(story.id)}
                          disabled={deleteStory.isPending}
                          aria-label={`Delete ${story.title}`}
                        >
                          <Trash2 className="size-3.5" aria-hidden="true" />
                        </Button>
                      </div>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      <span className="font-medium text-foreground">Situation: </span>
                      {story.situation}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      <span className="font-medium text-foreground">Result: </span>
                      {story.result}
                    </p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        );
      })}

      {(storiesQuery.data ?? []).length === 0 ? (
        <EmptyState icon={BookMarked} title="No stories yet" description="Add your first STAR story above to start building coverage." />
      ) : null}
    </div>
  );
}
