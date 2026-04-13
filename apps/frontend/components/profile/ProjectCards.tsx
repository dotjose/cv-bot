"use client";

import type { Project } from "@/lib/types";

export function ProjectCards({ projects }: { projects: Project[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {projects.map((p) => (
        <article
          key={p.id}
          className="cv-surface-card p-4 transition-[border-color,transform] duration-200 hover:border-white/[0.1] hover:shadow-[var(--shadow-card)]"
        >
          <h3 className="text-[15px] font-semibold tracking-tight text-zinc-50">{p.title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-[var(--color-fg-soft)]">
            {p.description}
          </p>
          {p.stack && p.stack.length > 0 ? (
            <ul className="mt-3 flex flex-wrap gap-1.5">
              {p.stack.map((s) => (
                <li
                  key={s}
                  className="rounded-md border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-[11px] text-zinc-400"
                >
                  {s}
                </li>
              ))}
            </ul>
          ) : null}
          {p.url ? (
            <a
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="cv-link mt-3 inline-block text-sm underline"
            >
              Link →
            </a>
          ) : null}
        </article>
      ))}
    </div>
  );
}
