# Epistemic Experiments Website — Implementation Design Doc

## Audience

This document is for a coding agent or developer implementing the first version of the Epistemic Experiments website.

The goal is to build a simple, maintainable, content-first website. Do not over-engineer it. The site should be easy for non-technical admins to update through Pages CMS, while the codebase stays small enough for one technical maintainer to understand.

---

## 1. Background

Epistemic Experiments is a small community hosting events, conversations, workshops, Q&As, coworking, and experiment logs around clearer thinking, AI, meditation, disagreement, education, community, and practical inquiry.

The website should act as:

1. a public landing page;
2. a place to show upcoming events;
3. an archive of past event summaries;
4. a public memory of what the community is learning;
5. a lightweight publishing system for admins.

The site should **not** become a custom community platform, member portal, event-management system, or full CMS application.

---

## 2. Core decision

Use:

```txt
Astro static site
Astro Cactus as the base theme
Pages CMS for content editing
Markdown/MDX content files in GitHub
GitHub Actions for validation and deployment
Luma manually for RSVPs/events
```

Pages CMS is only for content. Luma remains the RSVP/event operations tool. We are not using the Luma API because we do not want to pay for Luma automation right now.

---

## 3. Non-goals

Do **not** implement:

- Luma API integration;
- user accounts;
- member-only pages;
- comments;
- search in v1 unless already included by the base theme;
- dynamic backend;
- database;
- custom event registration;
- Discord/WhatsApp integration;
- automatic publishing to Luma;
- complex preview infrastructure.

A boring static site that is actually updated is better than a clever system that becomes a maintenance shrine.

---

## 4. High-level architecture

```txt
Pages CMS
  edits Markdown/YAML files in GitHub
        ↓
GitHub repository
  stores content, media, code, and history
        ↓
GitHub Actions
  validates content and builds Astro site
        ↓
Static hosting
  GitHub Pages initially; Cloudflare Pages optional later
        ↓
Public website
```

Manual event workflow:

```txt
Create event draft in Pages CMS
  ↓
Review/finalize copy
  ↓
Create Luma event manually
  ↓
Paste Luma URL back into Pages CMS
  ↓
Mark event live
  ↓
Site deploys
```

---

## 5. Design direction

Target style:

> Warm illustrated explainer archive.

The site should feel like a thoughtful personal publication, not a SaaS product. It should combine:

- warm serif typography;
- simple article layouts;
- wholesome explanatory diagrams;
- watercolor/cartographic hero images;
- muted colors;
- minimal UI chrome;
- clear writing hierarchy.

Visual references:

- Daniel Miessler-style article structure: title, italic subtitle, date, tags, image, long-form explanation.
- Borretti-style literary essay simplicity: serif text, narrow column, little clutter.
- EE generated images: watercolor landscape, map/territory overlays, field-guide atmosphere.

Do **not** copy another site’s branding, exact layout, or proprietary fonts. Use the references only as directional inspiration.

---

## 6. Typography

Use **Spectral** as the primary typeface.

Recommended pairing:

```txt
Body: Spectral 400
Headings: Spectral 500/600
Subtitles/quotes: Spectral Italic
Navigation/tags/metadata: IBM Plex Sans or IBM Plex Mono
```

Implementation option:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
```

Later, fonts can be self-hosted if desired. Do not block v1 on font self-hosting.

---

## 7. Color palette

Replace the default dark/hacker-blog feel of Astro Cactus with a warm paper palette.

```css
:root {
  --paper: #fbf8ef;
  --paper-soft: #f6f0e4;
  --surface: #f0eadb;

  --ink: #253044;
  --ink-soft: #3d4658;
  --muted: #74706a;
  --line: #d9d0bd;

  --blue: #334f8f;
  --blue-soft: #dbe4f2;
  --terracotta: #a86454;
  --sage: #7f8f78;
  --link: #9b4e67;
}
```

The site should default to light mode. Dark mode is optional, but do not let dark mode be the first impression.

---

## 8. CSS baseline

Apply a global style similar to this. Adapt to Astro Cactus’ existing CSS/Tailwind structure rather than fighting the theme.

```css
html {
  color-scheme: light;
}

body {
  background:
    radial-gradient(circle at top left, rgba(168, 100, 84, 0.08), transparent 34rem),
    radial-gradient(circle at bottom right, rgba(51, 79, 143, 0.06), transparent 38rem),
    var(--paper);
  color: var(--ink);
  font-family: "Spectral", Georgia, serif;
  font-size: 18px;
  line-height: 1.58;
  text-rendering: optimizeLegibility;
}

.site-header {
  max-width: 720px;
  margin: 1.5rem auto 0;
  padding: 0 1.25rem 0.65rem;
  border-bottom: 2px solid var(--blue);
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.site-title {
  color: var(--ink);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.site-nav {
  display: flex;
  gap: 1rem;
  align-items: center;
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.article {
  max-width: 680px;
  margin: 0 auto;
  padding: 2rem 1.25rem 5rem;
}

.article h1 {
  font-family: "Spectral", Georgia, serif;
  font-size: clamp(2.2rem, 8vw, 3.8rem);
  line-height: 0.98;
  letter-spacing: -0.035em;
  margin: 2rem 0 1rem;
}

.article .subtitle {
  color: var(--ink-soft);
  font-style: italic;
  font-size: 1.25rem;
  line-height: 1.35;
  margin-bottom: 1.5rem;
}

.article .meta,
.article .tags,
.tag,
.event-meta {
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  font-size: 0.82rem;
  color: var(--muted);
}

.article a,
a {
  color: var(--link);
  text-decoration-thickness: 0.06em;
  text-underline-offset: 0.16em;
}

.article h2 {
  font-size: 2rem;
  line-height: 1.1;
  margin-top: 3rem;
}

.article h3 {
  font-size: 1.35rem;
  margin-top: 2rem;
}

.article blockquote {
  margin: 2rem 0;
  padding-left: 1rem;
  border-left: 4px solid var(--blue);
  color: var(--muted);
  font-style: italic;
}

.article img,
.explainer-card {
  display: block;
  width: 100%;
  border-radius: 14px;
  background: var(--surface);
  border: 1px solid var(--line);
  margin: 2rem 0;
}

.card {
  background: rgba(255, 252, 245, 0.78);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(52, 47, 39, 0.06);
}

.tag {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--line);
  background: var(--paper-soft);
  color: var(--muted);
  border-radius: 999px;
  padding: 0.25rem 0.65rem;
}

.button-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--blue);
  color: #fffaf0;
  padding: 0.7rem 1rem;
  text-decoration: none;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  font-weight: 600;
}

.button-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid var(--line);
  color: var(--ink);
  padding: 0.7rem 1rem;
  text-decoration: none;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  font-weight: 600;
}
```

### Cactus-specific caveat

Astro Cactus sets the body to a monospace style. Remove the `font-mono` body class or equivalent setting. The site should not look like a developer terminal blog.

---

## 9. Pages and routing

Required v1 pages:

```txt
/
/about
/events
/logs
/resources
/join
```

Recommended naming in UI:

```txt
Home
Events
Experiment Logs
Resources
About
Join
```

### Home page

Purpose: explain EE quickly and route people to events/logs.

Sections:

1. Hero with title, short description, and watercolor map/territory image.
2. Upcoming events.
3. Latest experiment logs.
4. What we explore.
5. Join/propose CTA.

### About page

Purpose: explain the community, norms, and tone.

Use the second watercolor image or a quieter diagrammatic hero.

### Events page

Purpose: show live/upcoming events with Luma buttons.

Only show events where:

```ts
status === "live" && publish_on_site === true && Boolean(luma_url)
```

### Experiment Logs page

Purpose: archive public event summaries.

Show published logs only.

### Resources page

Purpose: annotated list of links, readings, tools, and references.

Avoid raw link dumps.

### Join page

Purpose: invite people into the event flow.

Do not publish WhatsApp, Discord, or raw meeting links by default. Point users to Luma or a contact/proposal form.

---

## 10. Content collections

Use Astro content collections for structure and validation.

Recommended collections:

```txt
src/content/events/
src/content/logs/
src/content/resources/
src/content/pages/
```

### Event content schema

Example file:

```txt
src/content/events/2026-04-05-making-sense-of-meditation.md
```

Example frontmatter:

```yaml
---
title: "Making Sense of Meditation"
slug: "making-sense-of-meditation"
status: "draft"

subtitle: "A practical Q&A on meditation, resistance, consistency, and what practice is actually for."
summary: "A practical Q&A about meditation through lived experience rather than theory."
description: |
  This session explores meditation through lived experience rather than theory.
  Bring questions about practice, resistance, pain, anxiety, consistency,
  and what meditation is actually for.

date: "2026-04-05"
time: "15:00"
timezone: "Asia/Kolkata"
duration_minutes: 90

format: "Online Q&A"
location_type: "online"
location_note: ""

host_display_name: "Chin"
host_public: true

topics:
  - meditation
  - inner work
  - practice

cover_image: "/images/events/meditation-qna.png"
luma_url: ""
publish_on_site: false

privacy_level: "normal"
recording_policy: "not_recorded"
---
```

Status values:

```txt
draft
review
ready_for_luma
live
completed
archived
cancelled
```

Visibility rule:

```ts
const isPublicEvent =
  event.data.status === "live" &&
  event.data.publish_on_site === true &&
  Boolean(event.data.luma_url);
```

### Experiment log schema

Example file:

```txt
src/content/logs/2026-04-05-making-sense-of-meditation.md
```

Example frontmatter:

```yaml
---
title: "Making Sense of Meditation"
slug: "making-sense-of-meditation"
subtitle: "What people actually ask when they ask about meditation."
date: "2026-04-05"
status: "draft"
related_event: "making-sense-of-meditation"
author: "EE Admin Team"

topics:
  - meditation
  - practice
  - inner work

cover_image: "/images/logs/meditation-map.png"
privacy_level: "sensitive"
---
```

Recommended log body:

```md
## Question explored

## What happened

## Key takeaways

## Interesting disagreements or tensions

## Open questions

## Resources shared

## Next experiment
```

Published logs must use:

```yaml
status: "published"
```

Only show logs with `status: "published"`.

### Resource schema

Example:

```yaml
---
title: "AI Risk Introductory Reading List"
slug: "ai-risk-introductory-reading-list"
status: "published"
url: "https://example.com"
source_type: "reading"
topics:
  - AI
  - risk
summary: "A short annotated resource for people new to AI risk discussions."
---
```

---

## 11. Suggested `content.config.ts`

Adapt this to the current Astro version and project structure.

```ts
import { defineCollection, z } from "astro:content";

const status = z.enum([
  "draft",
  "review",
  "ready_for_luma",
  "live",
  "completed",
  "archived",
  "cancelled",
  "published",
]);

const events = defineCollection({
  type: "content",
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
    date: z.string(),
    time: z.string().optional(),
    timezone: z.string().default("Asia/Kolkata"),
    duration_minutes: z.number().optional(),
    format: z.string().optional(),
    location_type: z.enum(["online", "in_person", "hybrid"]).optional(),
    location_note: z.string().optional(),
    host_display_name: z.string().optional(),
    host_public: z.boolean().default(true),
    topics: z.array(z.string()).default([]),
    cover_image: z.string().optional(),
    luma_url: z.string().url().or(z.literal("")).default(""),
    publish_on_site: z.boolean().default(false),
    privacy_level: z.enum(["normal", "sensitive"]).default("normal"),
    recording_policy: z.enum(["recorded", "not_recorded", "unknown"]).default("unknown"),
  }),
});

const logs = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    subtitle: z.string().optional(),
    date: z.string(),
    status: z.enum(["draft", "review", "published", "archived"]),
    related_event: z.string().optional(),
    author: z.string().default("EE Admin Team"),
    topics: z.array(z.string()).default([]),
    cover_image: z.string().optional(),
    privacy_level: z.enum(["normal", "sensitive"]).default("normal"),
  }),
});

const resources = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    status: z.enum(["draft", "published", "archived"]),
    url: z.string().url().optional(),
    source_type: z.string().optional(),
    topics: z.array(z.string()).default([]),
    summary: z.string(),
  }),
});

export const collections = { events, logs, resources };
```

Caveat: Astro content collection APIs can vary across versions. Use the installed Astro version’s expected syntax. Do not upgrade Astro unless necessary.

---

## 12. Pages CMS configuration

Create `.pages.yml` at the repo root.

Keep it simple. Expose only the fields admins need.

Example direction:

```yaml
media:
  input: public/images
  output: /images

content:
  - name: events
    label: Events
    type: collection
    path: src/content/events
    format: yaml-frontmatter
    filename: "{year}-{month}-{day}-{slug}.md"
    fields:
      - name: title
        label: Title
        type: string
        required: true
      - name: slug
        label: Slug
        type: string
        required: true
      - name: status
        label: Status
        type: select
        required: true
        default: draft
        options:
          values:
            - draft
            - review
            - ready_for_luma
            - live
            - completed
            - archived
            - cancelled
      - name: subtitle
        label: Subtitle
        type: string
      - name: summary
        label: Summary
        type: text
        required: true
      - name: description
        label: Description
        type: rich-text
      - name: date
        label: Date
        type: date
        required: true
      - name: time
        label: Time
        type: string
      - name: timezone
        label: Timezone
        type: string
        default: Asia/Kolkata
      - name: format
        label: Format
        type: string
      - name: host_display_name
        label: Host display name
        type: string
      - name: topics
        label: Topics
        type: string
        list: true
      - name: cover_image
        label: Cover image
        type: image
      - name: luma_url
        label: Luma URL
        type: string
      - name: publish_on_site
        label: Publish on site
        type: boolean
        default: false
      - name: privacy_level
        label: Privacy level
        type: select
        default: normal
        options:
          values:
            - normal
            - sensitive
      - name: recording_policy
        label: Recording policy
        type: select
        default: unknown
        options:
          values:
            - recorded
            - not_recorded
            - unknown
      - name: body
        label: Body
        type: rich-text

  - name: logs
    label: Experiment Logs
    type: collection
    path: src/content/logs
    format: yaml-frontmatter
    filename: "{year}-{month}-{day}-{slug}.md"
    fields:
      - name: title
        label: Title
        type: string
        required: true
      - name: slug
        label: Slug
        type: string
        required: true
      - name: subtitle
        label: Subtitle
        type: string
      - name: date
        label: Date
        type: date
        required: true
      - name: status
        label: Status
        type: select
        default: draft
        options:
          values:
            - draft
            - review
            - published
            - archived
      - name: related_event
        label: Related event slug
        type: string
      - name: topics
        label: Topics
        type: string
        list: true
      - name: cover_image
        label: Cover image
        type: image
      - name: privacy_level
        label: Privacy level
        type: select
        default: normal
        options:
          values:
            - normal
            - sensitive
      - name: body
        label: Body
        type: rich-text
```

Caveat: Verify Pages CMS field syntax against the installed/current Pages CMS docs. The coding agent should treat this as a starting config, not sacred scripture.

---

## 13. Manual Luma workflow

Luma is manual in v1.

Event lifecycle:

```txt
draft → review → ready_for_luma → live → completed → archived
```

Rules:

- `draft`: internal only.
- `review`: admins are checking copy.
- `ready_for_luma`: someone should manually create the Luma event.
- `live`: Luma URL is pasted and `publish_on_site` is true.
- `completed`: event happened; create or link an experiment log.
- `archived`: old event.
- `cancelled`: do not show as upcoming.

Manual Luma creation checklist:

```txt
[ ] Copy title from Pages CMS
[ ] Copy date/time/timezone
[ ] Copy summary/description
[ ] Upload/use cover image if desired
[ ] Set approval/visibility in Luma manually
[ ] Publish Luma event
[ ] Paste Luma URL back into Pages CMS
[ ] Set status: live
[ ] Set publish_on_site: true
```

Never publish a public event without a Luma URL.

---

## 14. Privacy and safety rules

The site may cover sensitive topics: meditation, mental health, dating, relationships, personal uncertainty, AI anxieties, private questions, etc.

Default rules:

- Do not publish WhatsApp/Discord invite links.
- Do not publish raw Google Meet links.
- Do not publish participant names unless explicitly approved.
- Do not include identifiable personal questions in recaps.
- Do not publish sensitive session details as transcripts.
- Sensitive sessions should use high-level summaries only.
- If in doubt, leave it out.

For `privacy_level: sensitive`, the UI may show a small note such as:

```txt
This log is a high-level summary. Personal questions and participant details are intentionally omitted.
```

---

## 15. GitHub Actions

Use two required workflows in v1:

1. validate content and build on PR/push;
2. deploy site on merge to `main`.

Optional later:

3. create a draft experiment log when an event is marked completed.

### 15.1 Validate workflow

Create:

```txt
.github/workflows/validate.yml
```

```yaml
name: Validate site

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Check formatting
        run: npm run format:check --if-present

      - name: Lint
        run: npm run lint --if-present

      - name: Build
        run: npm run build
```

If the project does not have lint/format scripts yet, do not create a complex lint setup. `npm run build` is the minimum required validation.

### 15.2 Deploy workflow for GitHub Pages

Create:

```txt
.github/workflows/deploy.yml
```

```yaml
name: Deploy site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

GitHub repository setting required:

```txt
Settings → Pages → Build and deployment → Source: GitHub Actions
```

### 15.3 Optional: create draft log after completed event

Do not implement this in v1 unless everything else is done.

If implemented, make it manual, not magical.

```txt
.github/workflows/create-log-draft.yml
```

Desired behavior:

```txt
Input: event slug
Find matching event file
Create src/content/logs/YYYY-MM-DD-event-slug.md if it does not exist
Pre-fill frontmatter and section headings
Open a PR
```

Do not auto-publish logs.

---

## 16. Astro config caveats

If deploying to a user/org GitHub Pages domain, normal config may be enough.

If deploying to a project page like:

```txt
https://username.github.io/repo-name/
```

then Astro may need:

```ts
export default defineConfig({
  site: "https://username.github.io",
  base: "/repo-name",
});
```

If using a custom domain, configure `site` accordingly and remove unnecessary `base`.

Common pitfall: broken assets on GitHub Pages due to incorrect `base` path.

---

## 17. Image handling

Use generated watercolor images for:

```txt
public/images/hero-map-territory.png
public/images/about-inquiry-landscape.png
```

Guidelines:

- Optimize large images before committing if possible.
- Prefer `.webp` or optimized `.jpg/.png` for hero images.
- Keep alt text meaningful.
- Do not use huge uncompressed files.
- Avoid placing critical text inside images.

Suggested alt text:

```txt
A watercolor landscape with a translucent map overlay, suggesting the relationship between models and reality.
```

---

## 18. Component list

Keep components minimal.

Required:

```txt
BaseLayout.astro
ArticleLayout.astro
HomeHero.astro
EventCard.astro
LogCard.astro
ResourceCard.astro
TagList.astro
```

Optional:

```txt
Callout.astro
Toc.astro
StatusBadge.astro
```

Do not introduce React unless a feature genuinely needs interactivity. Astro components are enough.

---

## 19. Homepage content structure

The homepage should roughly follow:

```txt
Hero
  Title: Epistemic Experiments
  Subtitle: Testing better ways to think, talk, and learn together.
  CTAs: Upcoming Events, Experiment Logs

Latest / Upcoming
  Upcoming event cards if any
  Fallback: link to Luma or Join page

Latest Experiment Logs
  3 newest published logs

What We Explore
  AI, meditation, disagreement, education, community, sensemaking

Join / Propose
  Attend an event or propose an experiment
```

Tone should be warm, clear, and non-grandiose.

Avoid copy like:

```txt
Join the future of consciousness.
```

Prefer:

```txt
A small community for testing better ways to think, talk, and learn together.
```

---

## 20. Article/log design

Experiment logs should feel like wholesome illustrated explainers.

Structure:

```txt
Site header
Title
Italic subtitle
Date + tags
Cover image / diagram
Intro paragraph
Sections
Resources
Next experiment
```

Recommended article frontmatter:

```yaml
title: "Making Sense of Meditation"
subtitle: "A practical Q&A on meditation, resistance, consistency, and what practice is actually for."
date: "2026-04-05"
topics: ["meditation", "inner work", "practice"]
cover_image: "/images/logs/meditation-map.png"
```

Article width:

```txt
max-width: 680px
```

Long lines are a readability bug. Do not make article text span the full screen.

---

## 21. Implementation order

Do this in order:

1. Start from Astro Cactus.
2. Remove or neutralize dark-first/monospace styling.
3. Add Spectral and the EE color palette.
4. Create basic routes: Home, About, Events, Logs, Resources, Join.
5. Create content collections and schemas.
6. Add sample content for one event, one log, and one resource.
7. Add Pages CMS config.
8. Add GitHub Actions validate workflow.
9. Add GitHub Pages deploy workflow.
10. Test local build.
11. Test Pages CMS editing flow.
12. Publish initial site.

Do not build optional automation until the basic editorial loop works.

---

## 22. Acceptance criteria

The implementation is done when:

```txt
[ ] Site builds locally with npm run build
[ ] Site deploys from GitHub Actions
[ ] Pages CMS can edit events and logs
[ ] Draft events do not appear publicly
[ ] Events require Luma URL before appearing publicly
[ ] Published logs appear on /logs
[ ] Sensitive logs can be marked sensitive
[ ] Home page shows hero image and latest content
[ ] Typography uses Spectral, not default monospace
[ ] Light warm palette is default
[ ] Mobile layout is readable
[ ] No private Discord/WhatsApp/Meet links are exposed
```

---

## 23. Main pitfalls for the coding agent

### Pitfall 1: Overengineering

Do not add a database, auth, API server, or Luma integration.

### Pitfall 2: Accidentally publishing drafts

Every public query must filter by status.

For events:

```ts
status === "live" && publish_on_site === true && luma_url
```

For logs:

```ts
status === "published"
```

### Pitfall 3: Breaking non-technical editing

Pages CMS fields should be understandable. Avoid exposing internal implementation fields unless needed.

Bad field name:

```txt
canonical_event_slug_resolved
```

Good field name:

```txt
Related event slug
```

### Pitfall 4: Cloning another site too closely

The design is inspired by warm explainer blogs and literary essays, but should not copy exact branding, fonts, or layout.

### Pitfall 5: Keeping Cactus too dark/monospace

The default Cactus aesthetic is not the desired EE identity. The final site should feel warm, illustrated, editorial, and approachable.

### Pitfall 6: GitHub Pages base path bugs

If assets break after deployment, check `site` and `base` in `astro.config`.

### Pitfall 7: Sensitive content leakage

Do not publish detailed personal disclosures from event logs. High-level summaries only for sensitive sessions.

### Pitfall 8: Too many components

A small set of clean components is better than a component zoo.

---

## 24. Final implementation brief

Build a simple Astro static site for Epistemic Experiments using Astro Cactus as a base. Restyle it into a warm, Spectral-based, light-mode-first publication with watercolor/cartographic imagery. Use Pages CMS as the content editing surface over Markdown files in GitHub. Keep Luma manual: event content is drafted in Pages CMS, copied manually to Luma, and the resulting Luma URL is pasted back before publishing on the site. Add GitHub Actions for validation and deployment only. Avoid dynamic backend features, automated Luma integration, and anything that makes non-technical editing harder.

The site should feel like a thoughtful illustrated publication for people trying to understand things together.

