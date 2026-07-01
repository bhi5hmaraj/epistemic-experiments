import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD.");

const events = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/events" }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    status: z.enum([
      "draft",
      "review",
      "ready_for_luma",
      "live",
      "completed",
      "archived",
      "cancelled",
    ]),
    subtitle: z.string().optional(),
    summary: z.string(),
    description: z.string().optional(),
    date,
    time: z.string().optional(),
    timezone: z.string().default("Asia/Kolkata"),
    duration_minutes: z.number().int().positive().optional(),
    format: z.string().optional(),
    location_type: z.enum(["online", "in_person", "hybrid"]).optional(),
    location_note: z.string().optional(),
    host_display_name: z.string().optional(),
    host_public: z.boolean().default(true),
    topics: z.array(z.string()).default([]),
    cover_image: z.string().optional(),
    luma_url: z.union([z.url(), z.literal("")]).default(""),
    publish_on_site: z.boolean().default(false),
    comments: z.boolean().default(true),
    privacy_level: z.enum(["normal", "sensitive"]).default("normal"),
    recording_policy: z
      .enum(["recorded", "not_recorded", "unknown"])
      .default("unknown"),
  }),
});

const logs = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/logs" }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    subtitle: z.string().optional(),
    date,
    status: z.enum(["draft", "review", "published", "archived"]),
    related_event: z.string().optional(),
    author: z.string().default("EE Admin Team"),
    topics: z.array(z.string()).default([]),
    cover_image: z.string().optional(),
    comments: z.boolean().default(true),
    privacy_level: z.enum(["normal", "sensitive"]).default("normal"),
  }),
});

const resources = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/resources" }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    status: z.enum(["draft", "published", "archived"]),
    url: z.url().optional(),
    source_type: z.string().optional(),
    topics: z.array(z.string()).default([]),
    summary: z.string(),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/pages" }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    description: z.string(),
  }),
});

export const collections = { events, logs, resources, pages };
