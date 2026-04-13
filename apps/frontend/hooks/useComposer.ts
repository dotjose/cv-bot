"use client";

import { useCallback, useState } from "react";

import { useChat } from "@/hooks/useChat";
import { useChatStore } from "@/store/chatStore";

export function useComposer() {
  const [draft, setDraft] = useState("");
  const isStreaming = useChatStore((s) => s.isStreaming);
  const { sendMessage } = useChat();

  const send = useCallback(() => {
    const t = draft.trim();
    if (!t || isStreaming) return;
    setDraft("");
    void sendMessage(t);
  }, [draft, isStreaming, sendMessage]);

  return { draft, setDraft, send, isStreaming };
}
