export interface Project {
  id: string;
  title: string;
  description: string;
  stack?: string[];
  url?: string;
}

export interface Experience {
  id: string;
  company: string;
  role: string;
  period: string;
  summary?: string;
}

export interface EducationEntry {
  id: string;
  institution: string;
  degree: string;
  period: string;
  details?: string;
}

/** GET /profile/overview */
export interface ProfileOverview {
  headline: string;
  summary: string;
}

/** API + store message union */
export type UserMessage = {
  id: string;
  role: "user";
  content: string;
};

export type AssistantTextMessage = {
  id: string;
  role: "assistant";
  content: string;
};

export type AssistantProjectCardsMessage = {
  id: string;
  role: "assistant";
  type: "project_cards";
  data: Project[];
};

export type AssistantSkillsMessage = {
  id: string;
  role: "assistant";
  type: "skills";
  data: string[];
};

export type AssistantTimelineMessage = {
  id: string;
  role: "assistant";
  type: "timeline";
  data: Experience[];
};

export type Message =
  | UserMessage
  | AssistantTextMessage
  | AssistantProjectCardsMessage
  | AssistantSkillsMessage
  | AssistantTimelineMessage;

export type ApiChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export function isAssistantText(m: Message): m is AssistantTextMessage {
  return m.role === "assistant" && "content" in m && !("type" in m);
}

export function messagesToApiHistory(messages: Message[]): ApiChatMessage[] {
  const flat: ApiChatMessage[] = [];
  for (const m of messages) {
    if (m.role === "user") {
      flat.push({ role: "user", content: m.content });
    } else if (isAssistantText(m) && m.content.length > 0) {
      flat.push({ role: "assistant", content: m.content });
    }
  }
  return flat.slice(-6);
}

/** GET /chat/sessions/{id} */
export interface ChatSessionDocument {
  session_id: string;
  created_at: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: string;
  }>;
}

export function messagesFromSessionDocument(doc: ChatSessionDocument): Message[] {
  const out: Message[] = [];
  let i = 0;
  for (const m of doc.messages) {
    if (m.role === "user") {
      out.push({
        id: `srv-u-${m.timestamp}-${i}`,
        role: "user",
        content: m.content,
      });
    } else {
      out.push({
        id: `srv-a-${m.timestamp}-${i}`,
        role: "assistant",
        content: m.content,
      });
    }
    i += 1;
  }
  return out;
}

/** Sidebar + main content: chat thread or structured CV slice */
export type NavId =
  | "chat"
  | "overview"
  | "projects"
  | "skills"
  | "experience"
  | "education"
  | "contact";
