"use client";

import type { GlossaryKey } from "@/lib/glossary";
import { Term } from "./Term";

/** A labelled numeric input. The label carries the tooltip, so the
 *  explanation sits where the question is asked. */
export function NumberField({
  label,
  glossary,
  value,
  onChange,
  min,
  max,
  step = 1,
  suffix,
  hint,
  disabled,
}: {
  label: string;
  glossary?: GlossaryKey;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  hint?: string;
  disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="block text-[13px] font-medium text-ink">
        {glossary ? <Term name={glossary}>{label}</Term> : label}
      </span>
      <span className="mt-1.5 flex items-baseline gap-1.5">
        <input
          type="number"
          value={Number.isFinite(value) ? value : ""}
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          onChange={(event) => {
            const parsed = Number.parseFloat(event.target.value);
            onChange(Number.isNaN(parsed) ? 0 : parsed);
          }}
          // A focused number input swallows the wheel and silently edits
          // itself, so scrolling past the form would quietly change the
          // experiment's parameters. Drop focus instead.
          onWheel={(event) => event.currentTarget.blur()}
          className="tnum w-full rounded-md border border-rule-strong bg-surface px-2.5 py-1.5 text-[15px] outline-none transition-colors focus:border-accent disabled:opacity-50"
        />
        {suffix && (
          <span className="shrink-0 text-[13px] text-ink-faint">{suffix}</span>
        )}
      </span>
      {hint && <span className="mt-1 block text-[12px] text-ink-faint">{hint}</span>}
    </label>
  );
}

/** A small segmented control. Used instead of a select — with two or three
 *  options, showing them all is faster to read than opening a menu. */
export function SegmentedField<T extends string>({
  label,
  glossary,
  value,
  options,
  onChange,
}: {
  label: string;
  glossary?: GlossaryKey;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <div>
      <span className="block text-[13px] font-medium text-ink">
        {glossary ? <Term name={glossary}>{label}</Term> : label}
      </span>
      <div
        role="radiogroup"
        aria-label={label}
        className="mt-1.5 inline-flex rounded-md border border-rule-strong bg-surface p-0.5"
      >
        {options.map((option) => {
          const active = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onChange(option.value)}
              className={`rounded px-3 py-1 text-[13px] transition-colors ${
                active
                  ? "bg-ink text-paper"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
