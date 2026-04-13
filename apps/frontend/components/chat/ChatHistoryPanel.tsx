"use client";

import { useCallback, useEffect, useState } from "react";

import { getChatSession, listChatSessions } from "@/lib/api";
import { messagesFromSessionDocument } from "@/lib/types";
import { useChatStore } from "@/store/chatStore";
import { useSessionStore } from "@/store/sessionStore";

import { cn } from "@/lib/cn";

function formatWhen(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

/**
 * Past sessions only — **New chat** is the primary button above in the sidebar (same session reset).
 */
export function ChatHistoryPanel() {
  const [open, setOpen] = useState(false);
  const [sessions, setSessions] = useState<Array<{ session_id: string; updated_at: string }>>([]);
  const sessionId = useSessionStore((s) => s.sessionId);
  const setSessionId = useSessionStore((s) => s.setSessionId);
  const replaceAllMessages = useChatStore((s) => s.replaceAllMessages);

  const load = useCallback(async () => {
    try {
      const r = await listChatSessions();
      setSessions(r.sessions);
    } catch {
      setSessions([]);
    }
  }, []);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  const select = async (id: string) => {
    try {
      const doc = await getChatSession(id);
      setSessionId(id);
      replaceAllMessages(messagesFromSessionDocument(doc));
      setOpen(false);
    } catch {
      /* */
    }
  };

  return (
    <div className="mt-1 min-w-0 shrink-0 border-t border-white/[0.05] pt-2">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full min-w-0 items-center justify-between gap-2 rounded-lg px-2 py-2 text-left text-[12px] font-medium text-zinc-400 transition-colors hover:bg-white/[0.04] hover:text-zinc-200"
      >
        <span className="truncate">Recent chats</span>
        <svg
          viewBox="0 0 24 24"
          className={cn("h-4 w-4 shrink-0 text-zinc-500 transition-transform", open && "rotate-180")}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open ? (
        <div className="mt-1 max-h-36 min-h-0 overflow-y-auto overscroll-y-contain rounded-lg border border-white/[0.06] bg-black/20 p-1">
          {sessions.length === 0 ? (
            <p className="px-2 py-3 text-center text-[11px] leading-relaxed text-zinc-500">
              No saved chats yet. Use <span className="text-zinc-400">New chat</span> above — history appears when
              storage is on.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {sessions.map((s) => {
                const active = sessionId === s.session_id;
                return (
                  <li key={s.session_id}>
                    <button
                      type="button"
                      className={cn(
                        "flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left text-[12px] transition-colors",
                        active
                          ? "bg-white/[0.08] text-zinc-100 ring-1 ring-inset ring-violet-500/20"
                          : "text-zinc-400 hover:bg-white/[0.05] hover:text-zinc-200"
                      )}
                      onClick={() => void select(s.session_id)}
                    >
                      <span
                        className={cn(
                          "mt-1.5 h-1 w-1 shrink-0 rounded-full",
                          active ? "bg-violet-400" : "bg-zinc-600"
                        )}
                        aria-hidden
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block font-mono text-[10px] tracking-tight text-zinc-300">
                          {s.session_id.slice(0, 8)}…
                        </span>
                        <span className="mt-0.5 block text-[10px] text-zinc-500">{formatWhen(s.updated_at)}</span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
