"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface SessionStore {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      sessionId: null,
      setSessionId: (sessionId) => set({ sessionId }),
    }),
    { name: "cv-bot-chat-session" }
  )
);
