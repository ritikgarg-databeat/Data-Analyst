"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckSquare,
  Info,
  Lightbulb,
  MessagesSquare,
  Square,
  XCircle,
} from "lucide-react";
import type {
  CalloutBlock,
  CalloutVariant,
  ChecklistBlock,
  CodeBlock,
  CodeLanguage,
  ComparisonBlock,
  ExampleBlock,
  FormulaBlock,
  HeadingBlock,
  ImageBlock,
  OutputBlock,
  TableBlock,
  TextBlock,
} from "@data-analyst-lab/shared";

import { cn } from "@/lib/utils";

import { InlineMarkdown } from "./inline-text";
import { highlightCode } from "./prism-highlight";
import "./prism-theme.css";

// ---------------------------------------------------------------------------
// text / heading
// ---------------------------------------------------------------------------

export function TextBlockView({ block }: { block: TextBlock }) {
  return <div className="text-sm leading-7 text-foreground">{InlineMarkdown({ text: block.body })}</div>;
}

export function HeadingBlockView({ block }: { block: HeadingBlock }) {
  const level = block.level ?? 2;
  const className = cn(
    "font-semibold tracking-tight text-foreground",
    level === 2 ? "text-xl" : "text-lg",
  );
  return level === 2 ? <h2 className={className}>{block.text}</h2> : <h3 className={className}>{block.text}</h3>;
}

// ---------------------------------------------------------------------------
// callout
// ---------------------------------------------------------------------------

const CALLOUT_STYLES: Record<
  CalloutVariant,
  { icon: typeof Info; label: string; wrapper: string; iconWrapper: string }
> = {
  important: {
    icon: Info,
    label: "Important",
    wrapper: "border-primary/30 bg-primary/5",
    iconWrapper: "bg-primary/10 text-primary",
  },
  tip: {
    icon: Lightbulb,
    label: "Tip",
    wrapper: "border-success/30 bg-success/5",
    iconWrapper: "bg-success/10 text-success",
  },
  warning: {
    icon: AlertTriangle,
    label: "Warning",
    wrapper: "border-warning/40 bg-warning/10",
    iconWrapper: "bg-warning/20 text-warning-foreground",
  },
  interview_tip: {
    icon: MessagesSquare,
    label: "Interview Tip",
    wrapper: "border-accent bg-accent/40",
    iconWrapper: "bg-accent text-accent-foreground",
  },
  common_mistake: {
    icon: XCircle,
    label: "Common Mistake",
    wrapper: "border-destructive/30 bg-destructive/5",
    iconWrapper: "bg-destructive/10 text-destructive",
  },
};

export function CalloutBlockView({ block }: { block: CalloutBlock }) {
  const style = CALLOUT_STYLES[block.variant];
  const Icon = style.icon;
  return (
    <div className={cn("flex gap-3 rounded-xl border px-4 py-3.5", style.wrapper)} role="note">
      <div className={cn("flex size-8 shrink-0 items-center justify-center rounded-full", style.iconWrapper)}>
        <Icon className="size-4" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1 text-sm leading-6 text-foreground">
        <p className="mb-0.5 text-xs font-semibold tracking-wide uppercase text-muted-foreground">
          {block.title ?? style.label}
        </p>
        {InlineMarkdown({ text: block.body })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// code / output
// ---------------------------------------------------------------------------

const LANGUAGE_LABEL: Record<CodeLanguage, string> = {
  sql: "SQL",
  python: "Python",
  javascript: "JavaScript",
  yaml: "YAML",
  json: "JSON",
  text: "Text",
};

export function CodePanel({ language, code, caption }: { language: CodeLanguage; code: string; caption?: string }) {
  const html = useMemo(() => highlightCode(code, language), [code, language]);
  return (
    <figure className="overflow-hidden rounded-xl border border-border bg-muted/40">
      <div className="flex items-center justify-between border-b border-border px-4 py-1.5 text-xs font-medium text-muted-foreground">
        <span>{LANGUAGE_LABEL[language]}</span>
      </div>
      <pre className="prism-code overflow-x-auto px-4 py-3 text-[0.83rem] leading-6">
        <code
          className={`language-${language}`}
          // Safe: `html` comes from Prism's own tokenizer run against our trusted content files, not user input.
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </pre>
      {caption ? (
        <figcaption className="border-t border-border px-4 py-2 text-xs text-muted-foreground">{caption}</figcaption>
      ) : null}
    </figure>
  );
}

export function CodeBlockView({ block }: { block: CodeBlock }) {
  return <CodePanel language={block.language} code={block.code} caption={block.caption} />;
}

export function OutputBlockView({ block }: { block: OutputBlock }) {
  return (
    <figure className="overflow-hidden rounded-xl border border-dashed border-border bg-card">
      <div className="border-b border-dashed border-border px-4 py-1.5 text-xs font-medium text-muted-foreground">
        Result
      </div>
      <pre className="overflow-x-auto px-4 py-3 font-mono text-[0.83rem] leading-6 whitespace-pre-wrap text-foreground">
        {block.body}
      </pre>
      {block.caption ? (
        <figcaption className="border-t border-dashed border-border px-4 py-2 text-xs text-muted-foreground">
          {block.caption}
        </figcaption>
      ) : null}
    </figure>
  );
}

// ---------------------------------------------------------------------------
// table / comparison
// ---------------------------------------------------------------------------

export function TableBlockView({ block }: { block: TableBlock }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[480px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
            {block.headers.map((header, index) => (
              <th key={index} scope="col" className="px-4 py-2.5">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {block.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-border last:border-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-2.5 text-foreground">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ComparisonBlockView({ block }: { block: ComparisonBlock }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <div className="border-b border-border bg-accent px-4 py-2.5 text-sm font-semibold text-accent-foreground">
        {block.title}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
              {block.columns.map((column, index) => (
                <th key={index} scope="col" className="px-4 py-2.5">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b border-border last:border-0">
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="px-4 py-2.5 text-foreground">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// formula / image / example
// ---------------------------------------------------------------------------

export function FormulaBlockView({ block }: { block: FormulaBlock }) {
  return (
    <div className="rounded-xl border border-border bg-muted/30 px-5 py-4">
      <p className="overflow-x-auto font-mono text-base font-medium tracking-tight text-foreground">
        {block.expression}
      </p>
      {block.description ? <p className="mt-2 text-sm text-muted-foreground">{block.description}</p> : null}
    </div>
  );
}

export function ImageBlockView({ block }: { block: ImageBlock }) {
  return (
    <figure>
      {/* eslint-disable-next-line @next/next/no-img-element -- lesson content images are arbitrary authored URLs, not build-time-known assets */}
      <img src={block.src} alt={block.alt} className="w-full rounded-xl border border-border" />
      {block.caption ? <figcaption className="mt-2 text-xs text-muted-foreground">{block.caption}</figcaption> : null}
    </figure>
  );
}

export function ExampleBlockView({ block }: { block: ExampleBlock }) {
  return (
    <div className="overflow-hidden rounded-xl border border-primary/25">
      <div className="border-b border-primary/25 bg-primary/5 px-4 py-2.5 text-sm font-semibold text-foreground">
        Worked Example — {block.title}
      </div>
      <div className="space-y-3 px-4 py-3.5 text-sm leading-7 text-foreground">
        {InlineMarkdown({ text: block.body })}
        {block.code ? <CodePanel language={block.language ?? "text"} code={block.code} /> : null}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// checklist (self-check reading aid — client-only state, never persisted)
// ---------------------------------------------------------------------------

export function ChecklistBlockView({ block }: { block: ChecklistBlock }) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3.5">
      {block.title ? <p className="mb-2 text-sm font-semibold text-foreground">{block.title}</p> : null}
      <ul className="space-y-2">
        {block.items.map((item, index) => {
          const isChecked = Boolean(checked[index]);
          return (
            <li key={index}>
              <button
                type="button"
                onClick={() => setChecked((prev) => ({ ...prev, [index]: !prev[index] }))}
                aria-pressed={isChecked}
                className="flex w-full items-start gap-2.5 rounded-md px-1 py-1 text-left text-sm hover:bg-muted/50"
              >
                {isChecked ? (
                  <CheckSquare className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
                ) : (
                  <Square className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                )}
                <span className={cn(isChecked && "text-muted-foreground line-through")}>{item}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
