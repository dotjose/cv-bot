"use client";

import { useCallback, useRef } from "react";

import { createChatSession, getApiBase, parseChatSseStream, postChatStream } from "@/lib/api";
import type {
  AssistantProjectCardsMessage,
  AssistantSkillsMessage,
  AssistantTimelineMessage,
  AssistantTextMessage,
  Experience,
  Message,
  Project,
} from "@/lib/types";
import { useChatStore } from "@/store/chatStore";
import { useSessionStore } from "@/store/sessionStore";

function newId(): string {
  return crypto.randomUUID();
}

function isProjectArray(x: unknown): x is Project[] {
  return (
    Array.isArray(x) &&
    x.every(
      (p) =>
        p &&
        typeof p === "object" &&
        "id" in p &&
        "title" in p &&
        typeof (p as Project).title === "string"
    )
  );
}

function isStringArray(x: unknown): x is string[] {
  return Array.isArray(x) && x.every((s) => typeof s === "string");
}

function isExperienceArray(x: unknown): x is Experience[] {
  return (
    Array.isArray(x) &&
    x.every(
      (e) =>
        e &&
        typeof e === "object" &&
        "company" in e &&
        typeof (e as Experience).company === "string"
    )
  );
}

function structuredMessageFromStream(
  type: "project_cards" | "skills" | "timeline",
  data: unknown
): Message | null {
  const id = newId();
  if (type === "project_cards" && isProjectArray(data)) {
    const msg: AssistantProjectCardsMessage = {
      id,
      role: "assistant",
      type: "project_cards",
      data,
    };
    return msg;
  }
  if (type === "skills" && isStringArray(data)) {
    const msg: AssistantSkillsMessage = {
      id,
      role: "assistant",
      type: "skills",
      data,
    };
    return msg;
  }
  if (type === "timeline" && isExperienceArray(data)) {
    const msg: AssistantTimelineMessage = {
      id,
      role: "assistant",
      type: "timeline",
      data,
    };
    return msg;
  }
  return null;
}

export function useChat() {
  const addMessage = useChatStore((s) => s.addMessage);
  const replaceMessage = useChatStore((s) => s.replaceMessage);
  const removeMessage = useChatStore((s) => s.removeMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const setError = useChatStore((s) => s.setError);

  const rafRef = useRef<number | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      if (!getApiBase()) {
        setError("Set NEXT_PUBLIC_API_URL to your API base URL.");
        return;
      }

      let sid = useSessionStore.getState().sessionId;
      if (!sid?.trim()) {
        try {
          const r = await createChatSession();
          sid = r.session_id;
          useSessionStore.getState().setSessionId(sid);
        } catch {
          sid = crypto.randomUUID();
          useSessionStore.getState().setSessionId(sid);
        }
      }

      const prior = useChatStore.getState().messages;

      setError(null);

      const userMsg: Message = {
        id: newId(),
        role: "user",
        content: trimmed,
      };
      addMessage(userMsg);

      const assistantId = newId();
      const assistantShell: AssistantTextMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
      };
      addMessage(assistantShell);
      setStreaming(true);

      const flushContent = (content: string) => {
        replaceMessage(assistantId, {
          id: assistantId,
          role: "assistant",
          content,
        });
      };

      const scheduleFlush = (acc: string) => {
        if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(() => {
          flushContent(acc);
          rafRef.current = null;
        });
      };

      try {
        const sid = useSessionStore.getState().sessionId;
        const res = await postChatStream(
          {
            message: trimmed,
            history: prior,
          },
          sid
        );

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(errText || `HTTP ${res.status}`);
        }
        if (!res.body) {
          throw new Error("No response body");
        }

        let acc = "";
        for await (const ev of parseChatSseStream(res.body)) {
          if (ev.kind === "text") {
            acc += ev.text;
            scheduleFlush(acc);
          } else if (ev.kind === "structured") {
            const extra = structuredMessageFromStream(ev.type, ev.data);
            if (extra) {
              addMessage(extra);
            }
          }
        }

        if (rafRef.current != null) {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = null;
        }
        flushContent(acc);

        if (!acc.trim()) {
          removeMessage(assistantId);
        }
      } catch (e: unknown) {
        if (rafRef.current != null) {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = null;
        }
        const msg = e instanceof Error ? e.message : "Request failed";
        setError(msg);
        removeMessage(assistantId);
      } finally {
        setStreaming(false);
      }
    },
    [addMessage, removeMessage, replaceMessage, setError, setStreaming]
  );

  return { sendMessage };
}
