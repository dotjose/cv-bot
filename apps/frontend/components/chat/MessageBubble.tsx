"use client";

import { memo } from "react";

import { cn } from "@/lib/cn";
import type { Message } from "@/lib/types";
import { isAssistantText } from "@/lib/types";

import { StreamingCaret } from "./StreamingMessage";

function MessageBody({ text, className }: { text: string; className?: string }) {
  const parts = text.split(/\n\n+/);
  if (parts.length <= 1) {
    return (
      <p className={cn("whitespace-pre-wrap leading-[1.65] last:mb-0", className)}>
        {text}
      </p>
    );
  }
  return (
    <div className={cn("space-y-3 leading-[1.65]", className)}>
      {parts.map((block, i) => (
        <p key={i} className="whitespace-pre-wrap last:mb-0">
          {block}
        </p>
      ))}
    </div>
  );
}

export const MessageBubble = memo(function MessageBubble({
  message,
  showStreamCaret,
}: {
  message: Message;
  showStreamCaret?: boolean;
}) {
  if (message.role === "user") {
    return (
      <div className="cv-message-in flex justify-end">
        <div
          className={cn(
            "max-w-[min(100%,42rem)] rounded-2xl rounded-br-md px-4 py-3.5 sm:px-5 sm:py-4",
            "border border-white/[0.07] bg-gradient-to-br from-zinc-700/90 to-zinc-800/95 text-zinc-50",
            "shadow-[var(--shadow-inset-highlight)]"
          )}
        >
          <MessageBody text={message.content} className="text-[15px]" />
        </div>
      </div>
    );
  }

  if (isAssistantText(message)) {
    return (
      <div className="cv-message-in flex justify-start">
        <div
          className={cn(
            "max-w-[min(100%,42rem)] rounded-2xl rounded-bl-md px-4 py-3.5 sm:px-5 sm:py-4",
            "border border-white/[0.06] bg-[var(--color-assistant-bubble)] text-zinc-200",
            "shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset,0_8px_24px_-12px_rgba(0,0,0,0.45)]"
          )}
        >
          <div className="text-[15px] text-zinc-200">
            {message.content ? (
              <MessageBody text={message.content} />
            ) : showStreamCaret ? (
              <span className="inline-flex min-h-[1.5em] items-center text-[var(--color-muted)]">
                <StreamingCaret />
              </span>
            ) : null}
            {message.content && showStreamCaret ? <StreamingCaret /> : null}
          </div>
        </div>
      </div>
    );
  }

  if (message.type === "project_cards") {
    return (
      <div className="cv-message-in flex justify-start">
        <div className="max-w-[min(100%,42rem)] space-y-3">
          {message.data.map((p) => (
            <div
              key={p.id}
              className="cv-surface-card px-4 py-3.5 text-[15px]"
            >
              <p className="font-medium text-zinc-50">{p.title}</p>
              <p className="mt-2 text-[var(--color-fg-soft)]">{p.description}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (message.type === "skills") {
    return (
      <div className="cv-message-in flex justify-start">
        <div className="flex max-w-[min(100%,42rem)] flex-wrap gap-2">
          {message.data.map((s) => (
            <span
              key={s}
              className="rounded-full border border-white/[0.08] bg-[var(--color-surface)]/90 px-3 py-1.5 text-sm text-zinc-200 shadow-[var(--shadow-inset-highlight)]"
            >
              {s}
            </span>
          ))}
        </div>
      </div>
    );
  }

  if (message.type === "timeline") {
    return (
      <div className="cv-message-in flex justify-start">
        <div className="max-w-[min(100%,42rem)] space-y-5 border-l border-violet-500/25 pl-4">
          {message.data.map((e) => (
            <div key={e.id}>
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">
                {e.period}
              </p>
              <p className="mt-1 text-[15px] font-medium text-zinc-50">{e.role}</p>
              <p className="text-sm text-[var(--color-fg-soft)]">{e.company}</p>
              {e.summary ? (
                <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">
                  {e.summary}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
});
