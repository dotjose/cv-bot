import type {
  ChatSessionDocument,
  EducationEntry,
  Experience,
  ProfileOverview,
  Project,
} from "./types";
import type { Message } from "./types";
import { messagesToApiHistory } from "./types";

/** When `NEXT_PUBLIC_API_URL` is missing from the client bundle, local `next dev` still works. */
const DEV_DEFAULT_API_BASE = "http://localhost:8787";

/**
 * Base URL for FastAPI (no trailing slash).
 * Prefer `NEXT_PUBLIC_API_URL` in `.env*` or CI; in development, fall back if the var was not inlined.
 */
export function getApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (raw) return raw.replace(/\/$/, "");
  if (process.env.NODE_ENV === "development") {
    return DEV_DEFAULT_API_BASE;
  }
  return "";
}

async function getJson<T>(path: string): Promise<T> {
  const base = getApiBase();
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  const res = await fetch(`${base}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `GET ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getProfileOverview(): Promise<ProfileOverview> {
  return getJson<ProfileOverview>("/profile/overview");
}

export function getProfileSkills(): Promise<{ skills: string[] }> {
  return getJson<{ skills: string[] }>("/profile/skills");
}

export function getProfileProjects(): Promise<{ projects: Project[] }> {
  return getJson<{ projects: Project[] }>("/profile/projects");
}

export function getProfileExperience(): Promise<{ experience: Experience[] }> {
  return getJson<{ experience: Experience[] }>("/profile/experience");
}

export function getProfileEducation(): Promise<{ education: EducationEntry[] }> {
  return getJson<{ education: EducationEntry[] }>("/profile/education");
}

export async function postChatReset(): Promise<void> {
  const base = getApiBase();
  if (!base) return;
  await fetch(`${base}/chat/reset`, { method: "POST" });
}

export async function createChatSession(): Promise<{ session_id: string }> {
  const base = getApiBase();
  if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");
  const res = await fetch(`${base}/chat/sessions`, { method: "POST" });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `create session failed: ${res.status}`);
  }
  return res.json() as Promise<{ session_id: string }>;
}

export async function listChatSessions(): Promise<{
  sessions: Array<{ session_id: string; updated_at: string }>;
}> {
  return getJson("/chat/sessions");
}

export function getChatSession(sessionId: string): Promise<ChatSessionDocument> {
  return getJson<ChatSessionDocument>(`/chat/sessions/${encodeURIComponent(sessionId)}`);
}

export type StreamStructuredType = "project_cards" | "skills" | "timeline";

export type StreamEvent =
  | { kind: "text"; text: string }
  | {
      kind: "structured";
      type: StreamStructuredType;
      data: unknown;
    }
  | { kind: "done" };

function parseDataLine(payload: string): StreamEvent | null {
  if (payload === "[DONE]") return { kind: "done" };
  try {
    const json = JSON.parse(payload) as {
      text?: string;
      type?: StreamStructuredType;
      data?: unknown;
    };
    if (json.type && json.data !== undefined) {
      return { kind: "structured", type: json.type, data: json.data };
    }
    if (json.text) {
      return { kind: "text", text: json.text };
    }
    return null;
  } catch {
    return null;
  }
}

export async function* parseChatSseStream(
  body: ReadableStream<Uint8Array>
): AsyncGenerator<StreamEvent, void, undefined> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";

    for (const block of parts) {
      const line = block.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      const ev = parseDataLine(payload);
      if (ev) yield ev;
    }
  }
}

export interface ChatRequest {
  message: string;
  history: Message[];
}

export async function postChatStream(
  req: ChatRequest,
  sessionId?: string | null
): Promise<Response> {
  const base = getApiBase();
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  const history = messagesToApiHistory(req.history);
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (sessionId?.trim()) {
    headers["X-Session-Id"] = sessionId.trim();
  }
  return fetch(`${base}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message: req.message, history }),
  });
}
