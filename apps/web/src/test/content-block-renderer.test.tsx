import { describe, expect, it } from "vitest";
import { fireEvent, screen } from "@testing-library/react";
import type { ContentBlock } from "@data-analyst-lab/shared";

import { ContentBlockRenderer, extractHeadings } from "@/components/features/lesson-reader/content-block-renderer";

import { renderWithProviders } from "./test-utils";

const BLOCKS: ContentBlock[] = [
  { type: "heading", text: "Section One", level: 2 },
  { type: "text", body: "Plain **bold** text with a [link](https://example.com)." },
  {
    type: "callout",
    variant: "warning",
    title: "Careful",
    body: "This is a warning callout.",
  },
  { type: "code", language: "sql", code: "SELECT 1;" },
  {
    type: "question",
    prompt: "What is 1 + 1?",
    choices: ["1", "2", "3"],
    correct_index: 1,
    explanation: "Basic arithmetic.",
  },
];

describe("ContentBlockRenderer", () => {
  it("renders every block type without crashing", () => {
    const { container } = renderWithProviders(<ContentBlockRenderer blocks={BLOCKS} />);

    expect(screen.getByRole("heading", { name: "Section One" })).toBeInTheDocument();
    expect(screen.getByText(/Plain/)).toBeInTheDocument();
    expect(screen.getByText("Careful")).toBeInTheDocument();
    // Prism splits "SELECT 1;" into multiple syntax-highlighting spans, so
    // check the code block's rendered text content rather than a single node.
    expect(container.querySelector("pre")?.textContent).toContain("SELECT 1;");
    expect(screen.getByText("What is 1 + 1?")).toBeInTheDocument();
  });

  it("renders inline markdown (bold, link) inside a text block", () => {
    renderWithProviders(<ContentBlockRenderer blocks={BLOCKS} />);

    const link = screen.getByRole("link", { name: "link" });
    expect(link).toHaveAttribute("href", "https://example.com");
    expect(screen.getByText("bold")).toBeInTheDocument();
  });

  it("grades the inline question block correctly against correct_index", () => {
    renderWithProviders(<ContentBlockRenderer blocks={BLOCKS} />);

    fireEvent.click(screen.getByRole("radio", { name: "2" }));

    expect(screen.getByText("Correct!")).toBeInTheDocument();
    expect(screen.getByText("Basic arithmetic.")).toBeInTheDocument();
  });

  it("shows an incorrect result when the wrong choice is picked", () => {
    renderWithProviders(<ContentBlockRenderer blocks={BLOCKS} />);

    fireEvent.click(screen.getByRole("radio", { name: "3" }));

    expect(screen.getByText("Not quite.")).toBeInTheDocument();
  });
});

describe("extractHeadings", () => {
  it("pulls out only heading blocks, preserving their block index", () => {
    const headings = extractHeadings(BLOCKS);

    expect(headings).toEqual([{ blockIndex: 0, text: "Section One", level: 2 }]);
  });
});
