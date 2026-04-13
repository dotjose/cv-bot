/**
 * STATIC profile layer — never fetched from API.
 * Edit for deployment / HF Space branding.
 */
export const STATIC_PROFILE = {
  name: "Eyosiyas Tadele",
  role: "Senior Full-Stack Engineer",
  email: "tdjosy@gmail.com",
  phone: "+251-923-52-22-53",
  website: "https://jose-dev-six.vercel.app",
  linkedIn: "https://linkedin.com/in/eyosiyas-tadele",
  address: "",
  /** Capability line (not job-search status) */
  availability: "Open to full-stack roles",
  availabilityDetail:
    "I focus on shipping NestJS/Node services, AI-powered backend services, Kafka/Redis pipelines, React/Next UIs, and production-grade integrations.",
} as const;

export type StaticProfile = typeof STATIC_PROFILE;
