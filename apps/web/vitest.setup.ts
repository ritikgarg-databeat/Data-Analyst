import "@testing-library/jest-dom/vitest";

// jsdom does not implement matchMedia — next-themes (and any responsive
// hooks) rely on it being present, so polyfill a minimal version.
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}
