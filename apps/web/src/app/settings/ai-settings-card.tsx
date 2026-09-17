"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAISettings, useAIUsage, useUpdateAISettings } from "@/features/ai/use-ai";

/**
 * AI Settings (spec section 48) — enable/disable, provider override,
 * response style, learning mode, privacy preference, plus today's usage
 * (spec section 42). Added as another Card on the existing /settings page
 * rather than a new route, matching that page's own established pattern.
 */
export function AISettingsCard() {
  const settingsQuery = useAISettings();
  const usageQuery = useAIUsage();
  const updateSettings = useUpdateAISettings();

  if (settingsQuery.isLoading) {
    return (
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>AI Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  const settings = settingsQuery.data;
  if (!settings) return null;

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>AI Settings</CardTitle>
        <CardDescription>
          This platform&apos;s AI features may send selected learning/code/data context to the configured AI
          provider. Nothing is sent when AI is disabled.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="size-4"
            checked={settings.enabled}
            onChange={(event) => updateSettings.mutate({ enabled: event.target.checked })}
          />
          Enable AI features
        </label>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ai-response-style">Response style</Label>
            <Select
              id="ai-response-style"
              value={settings.response_style}
              onChange={(event) => updateSettings.mutate({ response_style: event.target.value })}
            >
              <option value="concise">Concise</option>
              <option value="balanced">Balanced</option>
              <option value="detailed">Detailed</option>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ai-learning-mode">Learning mode</Label>
            <Select
              id="ai-learning-mode"
              value={settings.learning_mode}
              onChange={(event) => updateSettings.mutate({ learning_mode: event.target.value })}
            >
              <option value="socratic">Socratic (hints before answers)</option>
              <option value="direct">Direct (answers first)</option>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ai-privacy">Privacy preference</Label>
            <Select
              id="ai-privacy"
              value={settings.privacy_preference}
              onChange={(event) => updateSettings.mutate({ privacy_preference: event.target.value })}
            >
              <option value="standard">Standard context</option>
              <option value="minimal">Minimal context only</option>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ai-provider">Provider</Label>
            <Select
              id="ai-provider"
              value={settings.provider_override ?? ""}
              onChange={(event) => updateSettings.mutate({ provider_override: event.target.value || null })}
            >
              <option value="">Use platform default ({settings.effective_provider})</option>
              <option value="local">Local (no network, no key needed)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </Select>
          </div>
        </div>

        {!settings.ai_configured || settings.effective_provider === "local" ? (
          <p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
            No API key is configured for the selected provider — set AI_API_KEY (or a provider-specific key) in
            the API&apos;s environment. AI features fall back to a local, no-network placeholder until then.
          </p>
        ) : null}

        {usageQuery.data ? (
          <div className="rounded-md border border-border p-3 text-sm">
            <p className="mb-1 font-medium text-foreground">AI usage today</p>
            <p className="text-muted-foreground">
              {usageQuery.data.request_count} of {usageQuery.data.daily_request_limit} requests used
              {" · "}
              {usageQuery.data.input_tokens + usageQuery.data.output_tokens} tokens
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
