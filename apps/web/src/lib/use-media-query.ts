"use client";

import { useCallback, useSyncExternalStore } from "react";

/**
 * Hydration-safe media query subscription for layouts that must change their
 * component structure (for example, resizable desktop panels becoming a
 * stacked mobile workspace).
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onStoreChange: () => void) => {
      if (typeof window === "undefined" || typeof window.matchMedia !== "function") return () => undefined;
      const media = window.matchMedia(query);
      media.addEventListener("change", onStoreChange);
      return () => media.removeEventListener("change", onStoreChange);
    },
    [query],
  );

  const getSnapshot = useCallback(
    () => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(query).matches,
    [query],
  );

  return useSyncExternalStore(subscribe, getSnapshot, () => false);
}
