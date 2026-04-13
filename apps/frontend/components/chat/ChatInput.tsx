"use client";

import { cn } from "@/lib/cn";

interface ChatInputProps {
  draft: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  draft,
  onChange,
  onSend,
  disabled,
  placeholder = "Message…",
}: ChatInputProps) {
  return (
    <form
      className="w-full"
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
    >
      <div
        className={cn(
          "relative flex min-h-[52px] items-end rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/95",
          "shadow-[var(--shadow-inset-highlight),0_2px_12px_-4px_rgba(0,0,0,0.35)]",
          "transition-[border-color,box-shadow] duration-200",
          "focus-within:border-violet-500/35 focus-within:shadow-[0_0_0_3px_rgba(124,58,237,0.18),var(--shadow-inset-highlight)]"
        )}
      >
        <label htmlFor="cv-chat-input" className="sr-only">
          Message
        </label>
        <textarea
          id="cv-chat-input"
          name="message"
          rows={1}
          value={draft}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder={placeholder}
          className={cn(
            "max-h-40 min-h-[52px] w-full resize-none bg-transparent py-3.5 pl-4 pr-[3.25rem] text-[15px] leading-relaxed",
            "text-zinc-100 placeholder:text-[var(--color-muted)]",
            "outline-none focus:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
        />
        <button
          type="submit"
          disabled={!draft.trim() || disabled}
          className={cn(
            "absolute bottom-2 right-2 flex items-center justify-center rounded-xl transition-all",
            "bg-gradient-to-br from-violet-600 to-indigo-600 text-white",
            "shadow-[var(--shadow-send)]",
            "hover:from-violet-500 hover:to-indigo-500 hover:brightness-[1.03]",
            "active:scale-[0.98]",
            "disabled:pointer-events-none disabled:opacity-35 disabled:shadow-none",
            "h-11 w-11 min-h-[44px] min-w-[44px] sm:h-9 sm:w-9 sm:min-h-0 sm:min-w-0"
          )}
          aria-label="Send"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="h-[18px] w-[18px] opacity-95"
            aria-hidden
          >
            <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
