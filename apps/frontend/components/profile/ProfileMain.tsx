"use client";

import { useEffect, useState } from "react";

import {
  getProfileEducation,
  getProfileExperience,
  getProfileOverview,
  getProfileProjects,
  getProfileSkills,
} from "@/lib/api";
import type {
  EducationEntry,
  Experience,
  ProfileOverview,
  Project,
} from "@/lib/types";
import type { NavId } from "@/lib/types";

import { STATIC_PROFILE } from "./ProfileConfig";
import { ContactCard } from "./ContactCard";
import { EducationCard } from "./EducationCard";
import { ExperienceTimeline } from "./ExperienceTimeline";
import { ProjectCards } from "./ProjectCards";
import { SkillsPanel } from "./SkillsPanel";

function Loading() {
  return (
    <div className="animate-pulse space-y-3 py-4">
      <div className="h-4 w-1/3 rounded-lg bg-white/[0.06]" />
      <div className="h-3 w-full rounded-lg bg-white/[0.04]" />
      <div className="h-3 w-5/6 rounded-lg bg-white/[0.04]" />
    </div>
  );
}

function Err({ message }: { message: string }) {
  return (
    <p className="rounded-xl border border-red-500/25 bg-red-950/30 px-4 py-3 text-sm text-red-200/95">
      {message}
    </p>
  );
}

export function ProfileMain({ section }: { section: Exclude<NavId, "chat"> }) {
  const [overview, setOverview] = useState<ProfileOverview | null>(null);
  const [skills, setSkills] = useState<string[] | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [experience, setExperience] = useState<Experience[] | null>(null);
  const [education, setEducation] = useState<EducationEntry[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const run = async () => {
      try {
        switch (section) {
          case "overview": {
            const o = await getProfileOverview();
            if (!cancelled) setOverview(o);
            break;
          }
          case "skills": {
            const r = await getProfileSkills();
            if (!cancelled) setSkills(r.skills);
            break;
          }
          case "projects": {
            const r = await getProfileProjects();
            if (!cancelled) setProjects(r.projects);
            break;
          }
          case "experience": {
            const r = await getProfileExperience();
            if (!cancelled) setExperience(r.experience);
            break;
          }
          case "education": {
            const r = await getProfileEducation();
            if (!cancelled) setEducation(r.education);
            break;
          }
          case "contact":
            if (!cancelled) {
              /* static only */
            }
            break;
          default:
            break;
        }
      } catch (e: unknown) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    if (section === "contact") {
      setLoading(false);
      return;
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [section]);

  if (section === "contact") {
    return <ContactCard profile={STATIC_PROFILE} />;
  }

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return <Err message={error} />;
  }

  if (section === "overview" && overview) {
    return (
      <div className="space-y-8">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]">
            About Me
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-zinc-50">
            {STATIC_PROFILE.name}
          </h2>
          <p className="mt-2 text-base text-[var(--color-fg-soft)]">{overview.headline}</p>
        </div>
        <div className="cv-surface-card p-5 sm:p-6">
          <h3 className="text-sm font-semibold text-zinc-100">Summary</h3>
          <p className="mt-3 text-[15px] leading-[1.7] text-zinc-400">
            {overview.summary}
          </p>
        </div>
      </div>
    );
  }

  if (section === "skills" && skills) {
    return (
      <div>
        <h2 className="text-lg font-semibold tracking-[-0.02em] text-zinc-50">Skills</h2>
        <div className="mt-6">
          <SkillsPanel skills={skills} />
        </div>
      </div>
    );
  }

  if (section === "projects" && projects) {
    return (
      <div>
        <h2 className="text-lg font-semibold tracking-[-0.02em] text-zinc-50">Projects</h2>
        <div className="mt-6">
          <ProjectCards projects={projects} />
        </div>
      </div>
    );
  }

  if (section === "experience" && experience) {
    return (
      <div>
        <h2 className="text-lg font-semibold tracking-[-0.02em] text-zinc-50">Experience</h2>
        <div className="mt-6">
          <ExperienceTimeline items={experience} />
        </div>
      </div>
    );
  }

  if (section === "education" && education) {
    return (
      <div>
        <h2 className="text-lg font-semibold tracking-[-0.02em] text-zinc-50">Education</h2>
        <div className="mt-6">
          <EducationCard entries={education} />
        </div>
      </div>
    );
  }

  return <Err message="No data" />;
}
