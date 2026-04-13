"use client";

import { cn } from "@/lib/cn";

export function SkillsPanel({
  skills,
  className,
}: {
  skills: string[];
  className?: string;
}) {
  return (
    <ul
      className={cn(
        "flex flex-wrap gap-2",
        className
      )}
    >
      {skills.map((s) => (
        <li
          key={s}
          className="rounded-full border border-white/[0.08] bg-[var(--color-surface)]/95 px-3.5 py-1.5 text-sm text-zinc-200 shadow-[var(--shadow-inset-highlight)] transition-colors duration-200 hover:border-violet-500/25 hover:text-zinc-50"
        >
          {s}
        </li>
      ))}
    </ul>
  );
}
