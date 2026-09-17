import type { ContentBlock } from "@data-analyst-lab/shared";

import {
  CalloutBlockView,
  ChecklistBlockView,
  CodeBlockView,
  ComparisonBlockView,
  ExampleBlockView,
  FormulaBlockView,
  HeadingBlockView,
  ImageBlockView,
  OutputBlockView,
  TableBlockView,
  TextBlockView,
} from "./content-blocks";
import { QuestionBlockView } from "./question-block";

export interface HeadingRef {
  blockIndex: number;
  text: string;
  level: 2 | 3;
}

/** Pulls out heading blocks (with their index) to build the reader's table of contents. */
export function extractHeadings(blocks: ContentBlock[]): HeadingRef[] {
  return blocks.reduce<HeadingRef[]>((acc, block, index) => {
    if (block.type === "heading") {
      acc.push({ blockIndex: index, text: block.text, level: block.level ?? 2 });
    }
    return acc;
  }, []);
}

function renderBlock(block: ContentBlock, index: number) {
  switch (block.type) {
    case "text":
      return <TextBlockView block={block} />;
    case "heading":
      return <HeadingBlockView block={block} />;
    case "callout":
      return <CalloutBlockView block={block} />;
    case "code":
      return <CodeBlockView block={block} />;
    case "output":
      return <OutputBlockView block={block} />;
    case "table":
      return <TableBlockView block={block} />;
    case "formula":
      return <FormulaBlockView block={block} />;
    case "image":
      return <ImageBlockView block={block} />;
    case "example":
      return <ExampleBlockView block={block} />;
    case "question":
      return <QuestionBlockView block={block} />;
    case "checklist":
      return <ChecklistBlockView block={block} />;
    case "comparison":
      return <ComparisonBlockView block={block} />;
    default: {
      // Exhaustiveness guard — a new block type must be added above.
      const _exhaustive: never = block;
      void _exhaustive;
      void index;
      return null;
    }
  }
}

interface ContentBlockRendererProps {
  blocks: ContentBlock[];
  /** Ref callback used by the lesson reader to observe each block for scroll/progress tracking. */
  registerBlockRef?: (index: number) => (el: HTMLDivElement | null) => void;
}

/** Renders an ordered list of lesson content blocks, each wrapped for scroll/progress tracking. */
export function ContentBlockRenderer({ blocks, registerBlockRef }: ContentBlockRendererProps) {
  return (
    <div className="space-y-5">
      {blocks.map((block, index) => (
        <div
          key={index}
          id={`block-${index}`}
          data-block-index={index}
          ref={registerBlockRef?.(index)}
        >
          {renderBlock(block, index)}
        </div>
      ))}
    </div>
  );
}
