import Prism from "prismjs";
// `clike` must load before `javascript`, which extends it.
import "prismjs/components/prism-clike";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-json";
import "prismjs/components/prism-python";
import "prismjs/components/prism-sql";
import "prismjs/components/prism-yaml";
import type { CodeLanguage } from "@data-analyst-lab/shared";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Highlights `code` for `language` via Prism's own tokenizer, returning safe HTML. */
export function highlightCode(code: string, language: CodeLanguage): string {
  const grammar = language === "text" ? undefined : Prism.languages[language];
  if (!grammar) {
    return escapeHtml(code);
  }
  return Prism.highlight(code, grammar, language);
}
