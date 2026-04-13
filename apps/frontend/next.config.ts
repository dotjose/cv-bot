import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { NextConfig } from "next";

const configDir = path.dirname(fileURLToPath(import.meta.url));

/** Monorepo root `.env` (two levels up from `apps/frontend`) — Next does not load it automatically. */
function readMonorepoRootNextPublicApiUrl(): string | undefined {
  const envPath = path.join(configDir, "..", "..", ".env");
  try {
    const raw = fs.readFileSync(envPath, "utf8");
    for (const line of raw.split("\n")) {
      const t = line.trim();
      if (!t || t.startsWith("#")) continue;
      const eq = t.indexOf("=");
      if (eq === -1) continue;
      const key = t.slice(0, eq).trim();
      if (key !== "NEXT_PUBLIC_API_URL") continue;
      let v = t.slice(eq + 1).trim();
      if (
        (v.startsWith('"') && v.endsWith('"')) ||
        (v.startsWith("'") && v.endsWith("'"))
      ) {
        v = v.slice(1, -1);
      }
      return v || undefined;
    }
  } catch {
    /* missing or unreadable */
  }
  return undefined;
}

const nextPublicApiUrl = (
  process.env.NEXT_PUBLIC_API_URL?.trim() ||
  readMonorepoRootNextPublicApiUrl()?.trim() ||
  "http://localhost:8787"
).replace(/\/$/, "");

/**
 * Monorepo: trace files from the workspace root so PostCSS/Tailwind resolve the same
 * whether you run `next build` from apps/frontend or `npm run build` inside that app.
 */
const outputFileTracingRoot = path.join(configDir, "../..");

/**
 * Static export uses absolute /_next/... URLs by default. If the site is served
 * from a subpath (S3 prefix, HF Space path, GitHub Pages project site), set
 * NEXT_PUBLIC_BASE_PATH (e.g. "/cv-bot") so JS/CSS load correctly. Without this,
 * chunks 404 → no hydration / no styles → looks like plain text.
 *
 * For local dev at http://localhost:3000/ leave NEXT_PUBLIC_BASE_PATH unset (or "").
 */
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const assetPrefix =
  process.env.NEXT_PUBLIC_ASSET_PREFIX ?? (basePath || undefined);

const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  outputFileTracingRoot,
  env: {
    NEXT_PUBLIC_API_URL: nextPublicApiUrl,
  },
  ...(basePath ? { basePath } : {}),
  ...(assetPrefix ? { assetPrefix } : {}),
};

export default nextConfig;
