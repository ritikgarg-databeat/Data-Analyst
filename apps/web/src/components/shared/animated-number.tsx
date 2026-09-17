"use client";

import { useEffect, useRef, useState } from "react";
import { animate, useReducedMotion } from "framer-motion";

interface AnimatedNumberProps {
  /** Final numeric value to count up (or down) to. */
  value: number;
  /** Optional formatter — defaults to a plain rounded integer. */
  format?: (value: number) => string;
  duration?: number;
  className?: string;
}

/** Counts up from its previous value to the new one whenever `value` changes. */
export function AnimatedNumber({ value, format, duration = 0.8, className }: AnimatedNumberProps) {
  const prefersReducedMotion = useReducedMotion();
  const [display, setDisplay] = useState(value);
  const previous = useRef(value);

  useEffect(() => {
    if (prefersReducedMotion) return;
    const controls = animate(previous.current, value, {
      duration,
      ease: "easeOut",
      onUpdate: (latest) => setDisplay(latest),
    });
    previous.current = value;
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const shown = prefersReducedMotion ? value : display;
  const formatted = format ? format(shown) : Math.round(shown).toString();
  return <span className={className}>{formatted}</span>;
}
