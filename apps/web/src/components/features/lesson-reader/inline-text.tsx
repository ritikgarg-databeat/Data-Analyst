import type { ReactNode } from "react";
import Link from "next/link";

/**
 * Hand-written, regex-based renderer for the small markdown-lite subset used
 * by lesson content bodies: **bold**, *italic*, `code`, and [text](url)
 * links. Deliberately not a markdown library — the content schema only ever
 * needs these four inline styles, plus blank-line paragraph breaks.
 *
 * Returns React nodes (never raw HTML), so there is no injection risk even
 * though lesson content is trusted.
 */
const INLINE_PATTERN = /(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`(.+?)`)|(\[(.+?)\]\((.+?)\))/g;

function renderInlineSegment(segment: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let matchIndex = 0;

  INLINE_PATTERN.lastIndex = 0;
  while ((match = INLINE_PATTERN.exec(segment)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(segment.slice(lastIndex, match.index));
    }

    const key = `${keyPrefix}-${matchIndex++}`;
    if (match[2] !== undefined) {
      nodes.push(<strong key={key}>{match[2]}</strong>);
    } else if (match[4] !== undefined) {
      nodes.push(<em key={key}>{match[4]}</em>);
    } else if (match[6] !== undefined) {
      nodes.push(
        <code key={key} className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]">
          {match[6]}
        </code>,
      );
    } else if (match[8] !== undefined && match[9] !== undefined) {
      const href = match[9];
      const isInternal = href.startsWith("/");
      nodes.push(
        isInternal ? (
          <Link key={key} href={href} className="text-primary underline underline-offset-2 hover:no-underline">
            {match[8]}
          </Link>
        ) : (
          <a
            key={key}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline underline-offset-2 hover:no-underline"
          >
            {match[8]}
          </a>
        ),
      );
    }

    lastIndex = INLINE_PATTERN.lastIndex;
  }

  if (lastIndex < segment.length) {
    nodes.push(segment.slice(lastIndex));
  }

  return nodes;
}

/** Renders a markdown-lite string as paragraphs (blank-line separated) with inline styling. */
export function InlineMarkdown({ text }: { text: string }): ReactNode {
  const paragraphs = text.split(/\n\s*\n/).filter((p) => p.trim().length > 0);
  const source = paragraphs.length > 0 ? paragraphs : [text];

  return (
    <>
      {source.map((paragraph, pIndex) => {
        const lines = paragraph.split("\n");
        return (
          <p key={pIndex} className={pIndex > 0 ? "mt-3" : undefined}>
            {lines.map((line, lIndex) => (
              <span key={lIndex}>
                {renderInlineSegment(line, `${pIndex}-${lIndex}`)}
                {lIndex < lines.length - 1 ? <br /> : null}
              </span>
            ))}
          </p>
        );
      })}
    </>
  );
}
