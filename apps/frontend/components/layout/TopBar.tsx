"use client";

import { useUiStore } from "@/store/uiStore";

import { STATIC_PROFILE } from "@/components/profile/ProfileConfig";

const TITLES: Record<string, string> = {
  chat: "Chat",
  overview: "About Me",
  experience: "Experience",
  skills: "Skills",
  projects: "Projects",
  education: "Education",
  contact: "Contact",
};

export function TopBar() {
  const setSidebarOpen = useUiStore((s) => s.setSidebarOpen);
  const activeView = useUiStore((s) => s.activeView);

  const title = TITLES[activeView] ?? "Chat";

  return (
    <header className="flex h-[3.25rem] shrink-0 items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-app-bg)]/85 px-3 backdrop-blur-md lg:hidden">
      <button
        type="button"
        aria-label="Open menu"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-zinc-300 transition-colors hover:bg-white/[0.06] hover:text-white"
        onClick={() => setSidebarOpen(true)}
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
        </svg>
      </button>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[15px] font-semibold tracking-[-0.02em] text-zinc-50">{title}</p>
        <p className="truncate text-xs text-[var(--color-muted)]">{STATIC_PROFILE.name}</p>
      </div>
    </header>
  );
}
