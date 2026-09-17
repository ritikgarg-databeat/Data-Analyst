"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Tracks which content blocks have scrolled into view via a single shared
 * IntersectionObserver, to drive both `last_position` (topmost visible
 * block) and `progress_percent` (highest block index ever seen / total).
 */
export function useBlockVisibility(totalBlocks: number) {
  const elementsRef = useRef(new Map<number, HTMLDivElement>());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const visibleSetRef = useRef(new Set<number>());
  const [maxIndexSeen, setMaxIndexSeen] = useState(-1);
  const [topVisibleIndex, setTopVisibleIndex] = useState(0);

  const registerBlockRef = useCallback(
    (index: number) => (el: HTMLDivElement | null) => {
      const elements = elementsRef.current;
      const previous = elements.get(index);
      if (previous && observerRef.current) {
        observerRef.current.unobserve(previous);
      }
      if (el) {
        elements.set(index, el);
        observerRef.current?.observe(el);
      } else {
        elements.delete(index);
        visibleSetRef.current.delete(index);
      }
    },
    [],
  );

  useEffect(() => {
    // Not implemented in jsdom/older browsers — degrade to "no live tracking" rather than crash.
    if (typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        let changed = false;
        for (const entry of entries) {
          const raw = (entry.target as HTMLElement).dataset.blockIndex;
          if (raw === undefined) continue;
          const index = Number(raw);
          if (entry.isIntersecting) {
            visibleSetRef.current.add(index);
          } else {
            visibleSetRef.current.delete(index);
          }
          changed = true;
        }
        if (!changed) return;
        const visible = Array.from(visibleSetRef.current);
        if (visible.length > 0) {
          setMaxIndexSeen((prev) => Math.max(prev, ...visible));
          setTopVisibleIndex(Math.min(...visible));
        }
      },
      { rootMargin: "0px 0px -55% 0px", threshold: 0 },
    );
    observerRef.current = observer;
    elementsRef.current.forEach((el) => observer.observe(el));

    return () => {
      observer.disconnect();
      observerRef.current = null;
    };
  }, []);

  const progressPercent =
    totalBlocks > 0 ? Math.min(100, Math.round(((maxIndexSeen + 1) / totalBlocks) * 100)) : 0;

  const scrollToBlock = useCallback((index: number) => {
    elementsRef.current.get(index)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  /** Marks a block index as seen immediately (used to seed from a restored `last_position`). */
  const markSeen = useCallback((index: number) => {
    setMaxIndexSeen((prev) => Math.max(prev, index));
  }, []);

  return { registerBlockRef, maxIndexSeen, topVisibleIndex, progressPercent, scrollToBlock, markSeen };
}
