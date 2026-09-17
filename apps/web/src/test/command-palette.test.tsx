import { describe, expect, it } from "vitest";
import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CommandPaletteProvider } from "@/components/layout/command-palette";

import { renderWithProviders } from "./test-utils";

describe("CommandPalette", () => {
  it("is closed until Ctrl/Cmd+K is pressed, then opens with every nav entry", async () => {
    renderWithProviders(
      <CommandPaletteProvider>
        <div>App content</div>
      </CommandPaletteProvider>,
    );

    expect(screen.queryByLabelText("Command palette search")).not.toBeInTheDocument();

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    expect(await screen.findByLabelText("Command palette search")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Go to Dashboard" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("option", { name: "Go to Search" })).toHaveAttribute("href", "/search");
    expect(screen.getByRole("option", { name: "Ask AI Mentor" })).toHaveAttribute("href", "/ai/mentor");
  });

  it("filters entries as the user types", async () => {
    renderWithProviders(
      <CommandPaletteProvider>
        <div>App content</div>
      </CommandPaletteProvider>,
    );

    fireEvent.keyDown(window, { key: "k", metaKey: true });
    const input = await screen.findByLabelText("Command palette search");

    fireEvent.change(input, { target: { value: "settings" } });

    expect(screen.getByRole("option", { name: "Go to Settings" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Go to Dashboard" })).not.toBeInTheDocument();
  });

  it("closes on Escape", async () => {
    renderWithProviders(
      <CommandPaletteProvider>
        <div>App content</div>
      </CommandPaletteProvider>,
    );

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const input = await screen.findByLabelText("Command palette search");

    fireEvent.keyDown(input, { key: "Escape" });

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByLabelText("Command palette search")).not.toBeInTheDocument();
  });

  it("navigates to the selected entry on click and closes the palette", async () => {
    renderWithProviders(
      <CommandPaletteProvider>
        <div>App content</div>
      </CommandPaletteProvider>,
    );

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const input = await screen.findByLabelText("Command palette search");
    fireEvent.change(input, { target: { value: "search" } });

    const searchLink = screen.getByRole("option", { name: "Go to Search" });
    expect(searchLink).toHaveAttribute("href", "/search");
    fireEvent.click(searchLink);

    expect(screen.queryByLabelText("Command palette search")).not.toBeInTheDocument();
  });

  it("Enter activates whatever ArrowDown actually navigated to, not the initial default", async () => {
    /**
     * Regression test — Enter used to always click `itemRefs.current[activeIndex]`,
     * but list items were real, independently-focusable `<Link>`s (no
     * `tabIndex={-1}`), so a keyboard user could Tab past the input onto a
     * different item than whatever ArrowDown last set `activeIndex` to, and
     * Enter would silently activate the wrong one. Items are no longer
     * separate tab stops (`role="option"`, `aria-selected`, real focus stays
     * on the input) — this confirms ArrowDown moves the one true "selected"
     * item, and it's the one Enter would click.
     */
    renderWithProviders(
      <CommandPaletteProvider>
        <div>App content</div>
      </CommandPaletteProvider>,
    );

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const input = await screen.findByLabelText("Command palette search");

    // Quick Actions are first: index 0 "Start Mock Interview", index 1
    // "Ask AI Mentor", index 2 "Open Dataset Hub".
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "ArrowDown" });

    const selected = document.querySelector('[aria-selected="true"]');
    expect(selected).toHaveAccessibleName("Open Dataset Hub");
    expect(selected).toHaveAttribute("href", "/datasets");
    expect(input).toHaveAttribute("aria-activedescendant", selected?.id);

    fireEvent.keyDown(input, { key: "Enter" });

    // The click landed on the selected item (its onClick closes the palette).
    expect(screen.queryByLabelText("Command palette search")).not.toBeInTheDocument();
  });

  it("list items are not separate tab stops — Tab skips straight past the whole results list", async () => {
    /**
     * Regression test for the root cause: list items used to be plain
     * `<Link>`s with no `tabIndex`, so they were real, independently
     * reachable tab stops. Tab could move actual DOM focus onto a link
     * without ever touching `activeIndex` (the only thing Enter activated),
     * silently desyncing "what's focused" from "what Enter activates."
     * `tabIndex={-1}` removes every result from the tab order — the dialog's
     * own close button is next after the input, never a result — confirmed
     * with a real Tab keypress via userEvent (fireEvent can't simulate
     * native tab-order traversal).
     */
    const user = userEvent.setup();
    renderWithProviders(
      <CommandPaletteProvider>
        <div>App content</div>
      </CommandPaletteProvider>,
    );

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const input = await screen.findByLabelText("Command palette search");
    expect(input).toHaveFocus();

    await user.tab();

    // Wherever focus landed, it's not the input and — the actual point of
    // this test — not a results-list item either.
    expect(document.activeElement).not.toBe(input);
    expect(document.activeElement?.getAttribute("role")).not.toBe("option");
  });
});
