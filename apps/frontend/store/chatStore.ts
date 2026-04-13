import { create } from "zustand";

import type { Message } from "@/lib/types";

const MAX_MESSAGES = 80;

export interface ChatStore {
  messages: Message[];
  isStreaming: boolean;
  error: string | null;

  addMessage: (m: Message) => void;
  replaceMessage: (id: string, m: Message) => void;
  removeMessage: (id: string) => void;
  clearError: () => void;
  setStreaming: (v: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
  replaceAllMessages: (messages: Message[]) => void;
}

export const useChatStore = create<ChatStore>()((set) => ({
  messages: [],
  isStreaming: false,
  error: null,

  addMessage: (m) =>
    set((s) => ({
      messages: [...s.messages, m].slice(-MAX_MESSAGES),
    })),

  replaceMessage: (id, m) =>
    set((s) => ({
      messages: s.messages.map((x) => (x.id === id ? m : x)),
    })),

  removeMessage: (id) =>
    set((s) => ({
      messages: s.messages.filter((x) => x.id !== id),
    })),

  clearError: () => set({ error: null }),

  setStreaming: (isStreaming) => set({ isStreaming }),

  setError: (error) => set({ error }),

  reset: () =>
    set({
      messages: [],
      isStreaming: false,
      error: null,
    }),

  replaceAllMessages: (messages) =>
    set({
      messages: messages.slice(-MAX_MESSAGES),
      isStreaming: false,
      error: null,
    }),
}));
