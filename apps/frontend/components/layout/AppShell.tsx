"use client";

import { useComposer } from "@/hooks/useComposer";
import { useHydrateChatSession } from "@/hooks/useHydrateChatSession";
import { useChatStore } from "@/store/chatStore";
import { useUiStore } from "@/store/uiStore";

import { ChatComposer } from "@/components/chat/ChatComposer";
import { MessageList } from "@/components/chat/MessageList";
import { ProfileMain } from "@/components/profile/ProfileMain";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

import { cn } from "@/lib/cn";

const mainCol = "mx-auto w-full max-w-[min(100%,51.25rem)] px-4 sm:px-5";

export function AppShell() {
  const activeView = useUiStore((s) => s.activeView);
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const setSidebarOpen = useUiStore((s) => s.setSidebarOpen);

  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);
  const clearError = useChatStore((s) => s.clearError);

  const { draft, setDraft, send, isStreaming: composerBusy } = useComposer();

  useHydrateChatSession();

  return (
    <div className="flex h-[100dvh] max-h-[100dvh] min-h-0 flex-col overflow-x-hidden bg-[var(--color-app-bg)]">
      <div className="flex min-h-0 flex-1 items-stretch">
        {sidebarOpen ? (
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-[2px] lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        ) : null}

        <div
          className={cn(
            "fixed inset-y-0 left-0 z-50 flex h-[100dvh] max-h-[100dvh] w-[min(17rem,88vw)] transition-transform duration-200 ease-out",
            "lg:static lg:z-0 lg:min-h-0 lg:w-auto lg:shrink-0 lg:translate-x-0",
            sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
          )}
        >
          <Sidebar className="min-h-0 w-full min-w-0 flex-1 lg:h-full" />
        </div>

        <div className="relative isolate flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div
            className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_100%_70%_at_50%_-25%,rgba(124,58,237,0.09),transparent_55%)]"
            aria-hidden
          />
          <TopBar />

          <main className="relative z-0 grid min-h-0 min-w-0 flex-1 grid-rows-[minmax(0,1fr)_auto]">
            <section
              aria-label={activeView === "chat" ? "Chat messages" : "Profile"}
              className="min-h-0 min-w-0 overflow-hidden"
            >
              <div className={cn(mainCol, "flex h-full min-h-0 min-w-0 flex-col")}>
                {activeView === "chat" ? (
                  <MessageList messages={messages} isStreaming={isStreaming} />
                ) : (
                  <div className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain py-6">
                    <ProfileMain section={activeView} />
                  </div>
                )}
              </div>
            </section>

            <div className="min-w-0 shrink-0">
              {error ? (
                <div
                  className="border-t border-red-500/20 bg-red-950/35 px-3 py-2.5 text-center text-sm text-red-200/95 backdrop-blur-sm"
                  role="alert"
                >
                  <span>{error}</span>
                  <button
                    type="button"
                    className="ml-2 rounded-md px-1.5 text-red-100/90 underline decoration-red-400/40 underline-offset-2 transition-colors hover:text-white"
                    onClick={clearError}
                  >
                    Dismiss
                  </button>
                </div>
              ) : null}

              <div className="border-t border-[var(--color-border)] bg-[var(--color-app-bg)]/90 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 shadow-[var(--shadow-dock)] backdrop-blur-md supports-[backdrop-filter]:bg-[var(--color-app-bg)]/75 sm:pb-4">
                <div className={mainCol}>
                  <ChatComposer
                    draft={draft}
                    setDraft={setDraft}
                    onSend={send}
                    disabled={composerBusy}
                    placeholder={
                      activeView === "chat"
                        ? "Message…"
                        : "Ask a question about this section…"
                    }
                  />
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
