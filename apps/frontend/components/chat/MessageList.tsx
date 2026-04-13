"use client";

import { memo, useEffect, useRef } from "react";

import type { Message } from "@/lib/types";
import { isAssistantText } from "@/lib/types";

import { MessageBubble } from "./MessageBubble";

export const MessageList = memo(function MessageList({
  messages,
  isStreaming,
}: {
  messages: Message[];
  isStreaming: boolean;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const streamingTailId =
    isStreaming && messages.length > 0
      ? (() => {
          const last = messages[messages.length - 1];
          return last && isAssistantText(last) ? last.id : undefined;
        })()
      : undefined;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  return (
    <div className="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-y-contain py-4 sm:py-6">
      <div className="flex w-full min-w-0 flex-col gap-5 sm:gap-6">
        {messages.length === 0 ? (
          <div className="cv-message-in px-2 py-8 text-center sm:py-12">
            <p className="text-[13px] font-medium uppercase tracking-[0.14em] text-[var(--color-muted)]">
              CV assistant
            </p>
            <p className="mx-auto mt-3 max-w-sm text-[15px] leading-relaxed text-[var(--color-fg-soft)]">
              Ask about experience, skills, or projects — or open a section from the sidebar.
            </p>
          </div>
        ) : null}
        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            message={m}
            showStreamCaret={Boolean(
              streamingTailId === m.id && isStreaming
            )}
          />
        ))}
        <div ref={bottomRef} className="h-px shrink-0" aria-hidden />
      </div>
    </div>
  );
});
