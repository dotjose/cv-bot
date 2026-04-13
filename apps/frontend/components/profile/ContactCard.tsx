"use client";

import type { StaticProfile } from "./ProfileConfig";

export function ContactCard({ profile }: { profile: StaticProfile }) {
  return (
    <div className="cv-surface-card p-5 sm:p-6">
      <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]">
        Contact
      </h2>
      <dl className="mt-4 space-y-3 text-[15px]">
        <div>
          <dt className="text-xs text-[var(--color-muted)]">Email</dt>
          <dd>
            <a href={`mailto:${profile.email}`} className="cv-link underline">
              {profile.email}
            </a>
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[var(--color-muted)]">Phone</dt>
          <dd className="text-zinc-200">{profile.phone}</dd>
        </div>
        <div>
          <dt className="text-xs text-[var(--color-muted)]">Website</dt>
          <dd>
            <a
              href={profile.website}
              target="_blank"
              rel="noopener noreferrer"
              className="cv-link underline"
            >
              {profile.website.replace(/^https?:\/\//, "")}
            </a>
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[var(--color-muted)]">LinkedIn</dt>
          <dd>
            <a
              href={profile.linkedIn}
              target="_blank"
              rel="noopener noreferrer"
              className="cv-link underline"
            >
              Profile
            </a>
          </dd>
        </div>
        {profile.address?.trim() ? (
          <div>
            <dt className="text-xs text-[var(--color-muted)]">Location</dt>
            <dd className="text-zinc-200">{profile.address}</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
