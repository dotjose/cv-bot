"use client";

import { createChatSession, postChatReset } from "@/lib/api";
import { useChatStore } from "@/store/chatStore";
import { useSessionStore } from "@/store/sessionStore";
import { useUiStore } from "@/store/uiStore";

export function useNewChat() {
  const reset = useChatStore((s) => s.reset);
  const setSessionId = useSessionStore((s) => s.setSessionId);

  return async () => {
    reset();
    try {
      await postChatReset();
    } catch {
      /* optional server call */
    }
    try {
      const { session_id } = await createChatSession();
      setSessionId(session_id);
    } catch {
      setSessionId(crypto.randomUUID());
    }
    useUiStore.getState().setActiveView("chat");
    useUiStore.getState().setSidebarOpen(false);
  };
}
