"use client";

import { cn } from "@/lib/cn";

export function StreamingCaret({ className }: { className?: string }) {
  return <span className={cn("cv-stream-caret", className)} aria-hidden />;
}
