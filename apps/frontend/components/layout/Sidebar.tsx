"use client";

import { useSyncExternalStore } from "react";

import { useNewChat } from "@/hooks/useNewChat";
import type { NavId } from "@/lib/types";
import { useUiStore } from "@/store/uiStore";

import { ChatHistoryPanel } from "@/components/chat/ChatHistoryPanel";
import { STATIC_PROFILE } from "@/components/profile/ProfileConfig";

import { cn } from "@/lib/cn";

const SECTION_NAV: { id: Exclude<NavId, "chat">; label: string; icon: IconName }[] = [
  { id: "overview", label: "About Me", icon: "user" },
  { id: "experience", label: "Experience", icon: "briefcase" },
  { id: "skills", label: "Skills", icon: "layers" },
  { id: "projects", label: "Projects", icon: "folder" },
  { id: "education", label: "Education", icon: "academic" },
  { id: "contact", label: "Contact", icon: "mail" },
];

type IconName = "user" | "briefcase" | "layers" | "folder" | "academic" | "mail" | "compose";

function useIsLg() {
  return useSyncExternalStore(
    (onStoreChange) => {
      if (typeof window === "undefined") return () => {};
      const mq = window.matchMedia("(min-width: 1024px)");
      mq.addEventListener("change", onStoreChange);
      return () => mq.removeEventListener("change", onStoreChange);
    },
    () =>
      typeof window !== "undefined"
        ? window.matchMedia("(min-width: 1024px)").matches
        : false,
    () => false
  );
}

function NavIcon({ name, className }: { name: IconName; className?: string }) {
  const c = cn("h-[18px] w-[18px] shrink-0", className);
  switch (name) {
    case "compose":
      return (
        <svg
          className={c}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <path d="M12 20h9" />
          <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
      );
    case "user":
      return (
        <svg className={c} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      );
    case "briefcase":
      return (
        <svg className={c} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
        </svg>
      );
    case "layers":
      return (
        <svg className={c} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z" />
          <path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12" />
          <path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17" />
        </svg>
      );
    case "folder":
      return (
        <svg className={c} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
        </svg>
      );
    case "academic":
      return (
        <svg className={c} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
          <path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5" />
        </svg>
      );
    case "mail":
      return (
        <svg className={c} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
          <path d="m22 6-10 7L2 6" />
        </svg>
      );
    default:
      return null;
  }
}

export function Sidebar({ className }: { className?: string }) {
  const activeView = useUiStore((s) => s.activeView);
  const setActiveView = useUiStore((s) => s.setActiveView);
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebarCollapsed = useUiStore((s) => s.toggleSidebarCollapsed);
  const newChat = useNewChat();
  const isLg = useIsLg();
  const collapsed = sidebarCollapsed && isLg;

  return (
    <nav
      className={cn(
        "flex min-h-0 min-w-0 h-full max-h-full w-full flex-col overflow-x-hidden border-r border-[var(--color-border)] bg-[var(--color-sidebar-bg)]",
        "transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] lg:w-[260px]",
        collapsed && "lg:w-[72px]",
        className
      )}
    >
      {/* Profile — tap to return to chat without clearing */}
      <button
        type="button"
        onClick={() => setActiveView("chat")}
        className={cn(
          "flex w-full shrink-0 border-b border-[var(--color-border)] text-left transition-colors hover:bg-white/[0.03]",
          collapsed ? "items-center justify-center px-2 py-4" : "gap-3 px-4 py-4"
        )}
        aria-label="Open chat"
      >
        <div
          className={cn(
            "flex shrink-0 items-center justify-center rounded-xl border border-white/[0.08] bg-gradient-to-br from-zinc-800/80 to-zinc-900/90 text-sm font-semibold tracking-tight text-zinc-100 shadow-[var(--shadow-inset-highlight)]",
            collapsed ? "h-10 w-10" : "h-11 w-11"
          )}
          aria-hidden
        >
          {STATIC_PROFILE.name
            .split(" ")
            .map((p) => p[0])
            .join("")
            .slice(0, 2)
            .toUpperCase()}
        </div>
        {!collapsed ? (
          <div className="min-w-0 flex-1">
            <p className="truncate text-[15px] font-semibold tracking-[-0.02em] text-zinc-50">
              {STATIC_PROFILE.name}
            </p>
            <p className="mt-0.5 truncate text-xs text-[var(--color-fg-soft)]">{STATIC_PROFILE.role}</p>
            <span
              className="mt-2 inline-flex max-w-full items-center truncate rounded-lg border border-emerald-500/15 bg-emerald-500/[0.07] px-2.5 py-0.5 text-[11px] font-medium tracking-wide text-emerald-300/95"
              title={STATIC_PROFILE.availability}
            >
              {STATIC_PROFILE.availability}
            </span>
          </div>
        ) : null}
      </button>

      <div
        className={cn(
          "flex min-h-0 min-w-0 flex-1 flex-col gap-1 overflow-y-auto overscroll-y-contain",
          collapsed ? "px-2 py-3" : "px-3 py-3"
        )}
      >
        <button
          type="button"
          onClick={() => void newChat()}
          aria-label="New chat"
          className={cn(
            "flex w-full items-center gap-3 rounded-xl border border-[var(--color-border)] bg-white/[0.03] text-left text-sm font-medium text-zinc-100 shadow-[var(--shadow-inset-highlight)] transition-all",
            "hover:border-white/[0.12] hover:bg-white/[0.06]",
            collapsed ? "justify-center px-0 py-3" : "px-3 py-2.5"
          )}
          title="New chat"
        >
          <NavIcon name="compose" className="text-[var(--color-accent-bright)]" />
          {!collapsed ? <span>New chat</span> : null}
        </button>

        {!collapsed ? <ChatHistoryPanel /> : null}

        <div className={cn("my-2 h-px bg-gradient-to-r from-transparent via-white/[0.08] to-transparent", collapsed ? "mx-1" : "mx-0")} />

        <p
          className={cn(
            "px-1 pb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]",
            collapsed && "sr-only"
          )}
        >
          Navigate
        </p>

        {SECTION_NAV.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              title={collapsed ? item.label : undefined}
              aria-current={isActive ? "page" : undefined}
              onClick={() => setActiveView(item.id)}
              className={cn(
                "relative flex w-full items-center gap-3 rounded-xl text-left text-sm transition-colors duration-200",
                collapsed ? "justify-center px-0 py-3" : "px-3 py-2.5",
                isActive
                  ? cn(
                      "bg-white/[0.07] text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]",
                      !collapsed &&
                        "before:absolute before:left-0 before:top-1/2 before:h-5 before:w-0.5 before:-translate-y-1/2 before:rounded-full before:bg-[var(--color-accent)] before:content-['']"
                    )
                  : "text-[var(--color-fg-soft)] hover:bg-white/[0.04] hover:text-zinc-100"
              )}
            >
              <NavIcon
                name={item.icon}
                className={isActive ? "text-[var(--color-accent-bright)]" : "text-zinc-500"}
              />
              {!collapsed ? <span>{item.label}</span> : null}
            </button>
          );
        })}
      </div>

      <div className={cn("shrink-0 border-t border-[var(--color-border)]", collapsed ? "p-2" : "p-3")}>
        <button
          type="button"
          onClick={toggleSidebarCollapsed}
          className={cn(
            "hidden w-full items-center justify-center gap-2 rounded-xl py-2 text-xs font-medium text-[var(--color-muted)] transition-colors hover:bg-white/[0.04] hover:text-zinc-300 lg:flex",
            collapsed ? "px-0" : "px-2"
          )}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg
            className={cn("h-4 w-4 transition-transform duration-200", collapsed && "rotate-180")}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
          {!collapsed ? <span>Collapse</span> : null}
        </button>
      </div>
    </nav>
  );
}
