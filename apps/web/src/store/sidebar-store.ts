import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SidebarState {
  /** Desktop sidebar collapsed (icon-only) state, persisted across sessions. */
  isCollapsed: boolean;
  toggleCollapsed: () => void;
  setCollapsed: (value: boolean) => void;
  /** Mobile slide-over sheet open state — intentionally not persisted. */
  isMobileOpen: boolean;
  setMobileOpen: (value: boolean) => void;
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
      isCollapsed: false,
      toggleCollapsed: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
      setCollapsed: (value) => set({ isCollapsed: value }),
      isMobileOpen: false,
      setMobileOpen: (value) => set({ isMobileOpen: value }),
    }),
    {
      name: "dal-sidebar",
      partialize: (state) => ({ isCollapsed: state.isCollapsed }),
    },
  ),
);
