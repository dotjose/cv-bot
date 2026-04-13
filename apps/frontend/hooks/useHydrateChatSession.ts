"use client";

import { useEffect } from "react";

import { getApiBase, getChatSession } from "@/lib/api";
import { messagesFromSessionDocument } from "@/lib/types";
import { useChatStore } from "@/store/chatStore";
import { useSessionStore } from "@/store/sessionStore";

/**
 * When ``sessionId`` is restored (persist) or changed, load the transcript from the API.
 */
export function useHydrateChatSession() {
  const sessionId = useSessionStore((s) => s.sessionId);

  useEffect(() => {
    const base = getApiBase();
    if (!sessionId?.trim() || !base) return;
    let cancelled = false;

    void (async () => {
      try {
        const doc = await getChatSession(sessionId);
        if (cancelled) return;
        if (doc.messages.length > 0) {
          useChatStore.getState().replaceAllMessages(messagesFromSessionDocument(doc));
        }
      } catch {
        if (!cancelled) {
          useSessionStore.getState().setSessionId(null);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);
}
