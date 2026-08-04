"use client";

import { useId, useState } from "react";
import { GLOSSARY, type GlossaryKey } from "@/lib/glossary";

/**
 * A statistical term with its plain-English definition on hover or focus.
 *
 * Keyboard-focusable and described via aria-describedby, because a definition
 * only reachable with a mouse isn't a definition for everyone.
 */
export function Term({
  name,
  children,
}: {
  name: GlossaryKey;
  children?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const entry = GLOSSARY[name];

  return (
    <span className="relative inline-block">
      <button
        type="button"
        aria-describedby={open ? id : undefined}
        className="cursor-help border-b border-dotted border-ink-faint pb-px text-left underline-offset-2 outline-none focus-visible:rounded-sm focus-visible:ring-2 focus-visible:ring-accent/40"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={(event) => {
          event.preventDefault();
          setOpen((previous) => !previous);
        }}
      >
        {children ?? entry.term}
      </button>

      {open && (
        <span
          id={id}
          role="tooltip"
          className="absolute bottom-[calc(100%+8px)] left-0 z-20 block w-72 rounded-md border border-rule-strong bg-surface px-3.5 py-2.5 text-[13px] font-normal leading-relaxed text-ink-muted shadow-[0_6px_20px_-6px_rgba(20,23,26,0.22)]"
        >
          <span className="mb-1 block text-[11px] uppercase tracking-[0.1em] text-ink-faint">
            {entry.term}
          </span>
          {entry.definition}
        </span>
      )}
    </span>
  );
}
