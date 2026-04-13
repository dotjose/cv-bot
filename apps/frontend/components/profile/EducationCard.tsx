"use client";

import type { EducationEntry } from "@/lib/types";

export function EducationCard({ entries }: { entries: EducationEntry[] }) {
  return (
    <div className="space-y-5">
      {entries.map((ed) => (
        <div key={ed.id} className="cv-surface-card p-4 sm:p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
            {ed.period}
          </p>
          <h3 className="mt-1 text-[15px] font-semibold tracking-tight text-zinc-50">
            {ed.degree}
          </h3>
          <p className="text-sm text-[var(--color-fg-soft)]">{ed.institution}</p>
          {ed.details ? (
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">
              {ed.details}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  );
}
