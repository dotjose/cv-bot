"use client";

import type { Experience } from "@/lib/types";

export function ExperienceTimeline({ items }: { items: Experience[] }) {
  return (
    <ol className="space-y-7 border-l border-violet-500/20 pl-5">
      {items.map((e) => (
        <li key={e.id} className="relative">
          <span className="absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 ring-[3px] ring-[var(--color-app-bg)]" />
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
            {e.period}
          </p>
          <p className="mt-1 text-[15px] font-semibold tracking-tight text-zinc-50">{e.role}</p>
          <p className="text-sm text-[var(--color-fg-soft)]">{e.company}</p>
          {e.summary ? (
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">{e.summary}</p>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
