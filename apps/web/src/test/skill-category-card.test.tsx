import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import { SkillCategoryCard } from "@/components/features/skills/skill-category-card";

import { renderWithProviders } from "./test-utils";

describe("SkillCategoryCard", () => {
  it("renders the label and a 0% bar when mastery data is absent", () => {
    renderWithProviders(<SkillCategoryCard label="SQL" />);

    expect(screen.getByText("SQL")).toBeInTheDocument();
    expect(screen.getByText("0% mastery")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
  });

  it("renders the correct percentage and skill count when mastery data is present", () => {
    renderWithProviders(<SkillCategoryCard label="Python" masteryPercent={67} skillCount={9} />);

    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("67% mastery")).toBeInTheDocument();
    expect(screen.getByText("9 skills")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "67");
  });
});
