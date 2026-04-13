"use client";

import { ChatInput } from "./ChatInput";

export function ChatComposer({
  draft,
  setDraft,
  onSend,
  disabled,
  placeholder,
}: {
  draft: string;
  setDraft: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  return (
    <ChatInput
      draft={draft}
      onChange={setDraft}
      onSend={onSend}
      disabled={disabled}
      placeholder={placeholder}
    />
  );
}
