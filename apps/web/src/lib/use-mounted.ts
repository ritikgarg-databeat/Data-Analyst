import { useSyncExternalStore } from "react";

function subscribe() {
  // The "mounted" flag never changes after the client snapshot is read, so
  // there is nothing to subscribe to — return a no-op unsubscribe.
  return () => {};
}

/**
 * True only once the component has hydrated on the client. Used to defer
 * client-only rendering (e.g. a theme-dependent icon) until after hydration
 * without the `setState` inside `useEffect` anti-pattern.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
