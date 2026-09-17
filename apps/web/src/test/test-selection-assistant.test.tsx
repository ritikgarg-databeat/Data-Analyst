import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen } from "@testing-library/react";

import { TestSelectionAssistant } from "@/components/features/statistics/test-selection-assistant";

import { renderWithProviders } from "./test-utils";

describe("TestSelectionAssistant", () => {
  it("suggests a two-proportion z-test for comparing conversion rates", () => {
    const onUseTest = vi.fn();
    renderWithProviders(<TestSelectionAssistant onUseTest={onUseTest} onUseCorrelation={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Two proportions (e.g. conversion rates)" }));
    expect(screen.getByText("Two-proportion z-test")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Use this test" }));
    expect(onUseTest).toHaveBeenCalledWith("two_proportion_z");
  });

  it("asks a follow-up normality question for two independent groups, then suggests Mann-Whitney if not normal", () => {
    const onUseTest = vi.fn();
    renderWithProviders(<TestSelectionAssistant onUseTest={onUseTest} onUseCorrelation={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Two independent groups" }));
    expect(screen.queryByText("Mann-Whitney U test")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "no" }));
    expect(screen.getByText("Mann-Whitney U test")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Use this test" }));
    expect(onUseTest).toHaveBeenCalledWith("mann_whitney");
  });

  it("routes a correlation suggestion through onUseCorrelation instead of onUseTest", () => {
    const onUseTest = vi.fn();
    const onUseCorrelation = vi.fn();
    renderWithProviders(<TestSelectionAssistant onUseTest={onUseTest} onUseCorrelation={onUseCorrelation} />);

    fireEvent.click(screen.getByRole("button", { name: "Two numeric variables (association)" }));
    fireEvent.click(screen.getByRole("button", { name: "yes" }));
    expect(screen.getByText("Pearson correlation")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Use this test" }));
    expect(onUseCorrelation).toHaveBeenCalledWith("pearson");
    expect(onUseTest).not.toHaveBeenCalled();
  });

  it("resets back to the first question", () => {
    renderWithProviders(<TestSelectionAssistant onUseTest={vi.fn()} onUseCorrelation={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "More than two groups" }));
    expect(screen.getByText("One-way ANOVA")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start over" }));
    expect(screen.queryByText("One-way ANOVA")).not.toBeInTheDocument();
  });
});
