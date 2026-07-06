# Epistemic Experiments Agent Guide

This repository contains the public website for Epistemic Experiments: a small,
content-first publication for events, experiment logs, and annotated resources.

Read this file before making product, design, content, or deployment changes.

## Sources Of Truth

Use these sources in this order:

1. This file for current implementation and maintenance decisions.
2. [`README.md`](README.md) for the editor and deployment workflow.
3. [`docs/ee_website_implementation_design_doc.md`](docs/ee_website_implementation_design_doc.md)
   for the original product and visual direction.
4. Existing code and content for established patterns.

The design document is directional, not immutable. Current decisions already
supersede two original examples:

- Deployment targets **Vercel**, not GitHub Pages.
- Accessibility-validated color tokens in `src/styles/global.css` supersede the
  original lower-contrast palette values.

## Product Constraints

Keep this a small static editorial website, not a community platform.

- Stack: Astro static output, Markdown content collections, Pages CMS, manual Luma workflow, Vercel hosting.
- Do not add a database, backend, authentication, event registration system, member area, Luma API integration, or messaging-platform integration without an explicit product decision.
- Content editors should be able to manage events, logs, resources, pages, and public images through Pages CMS.
- Prefer simple Astro components over client-side frameworks. Do not introduce React for static presentation.

## Design Direction

The intended identity is a **warm illustrated explainer archive**: thoughtful,
editorial, lightly field-guide-like, and approachable. It should not resemble a
SaaS landing page or a developer terminal blog.

### Typography

- Primary body and display face: `Spectral`.
- UI/navigation/metadata face: `IBM Plex Sans`.
- Eyebrow or very limited utility labels: `IBM Plex Mono`.
- Keep body copy readable and quiet; use the serif personality primarily through
  prose and headings rather than decorative treatments.
- Body copy is `1.125rem` with generous leading; avoid reverting to pixel-sized
  body typography.
- Keep long-form content narrow. Article prose is intentionally constrained to
  roughly `680px`; do not stretch articles across wide screens.
- Use `text-wrap: balance` for display/section headings and `text-wrap: pretty`
  for readable prose where supported.

### Color And Surfaces

Use the established light-first warm-paper palette in
[`src/styles/global.css`](src/styles/global.css). Important validated values:

```css
--paper: #fbf8ef;
--paper-soft: #f6f0e4;
--surface: #f0eadb;
--ink: #253044;
--ink-soft: #3d4658;
--muted: #68645d;
--line: #d9d0bd;
--line-strong: #8b8372;
--blue: #334f8f;
--terracotta: #965342;
--link: #9b4e67;
```

- `--line` is for subtle decorative separation, such as cards and image frames.
- `--line-strong` is for interactive component boundaries, because controls need
  stronger non-text contrast.
- Do not restore the earlier `--muted: #74706a` or `--terracotta: #a86454`
  values for small text; they failed contrast on warm surfaces.
- Avoid dark-mode-first changes. Light paper is the brand default.

### Imagery

- Use watercolor/cartographic imagery, observation paths, landscapes, vessels,
  plants, maps, and inquiry motifs.
- Public delivery assets belong in `public/images/`, preferably optimized `.webp`.
- High-resolution/local generation sources belong in ignored `assets_gen/`, not
  in version control.
- Current intentional placements:

| Asset | Role |
| --- | --- |
| `/images/community-map.webp` | Homepage hero |
| `/images/inquiry-garden.webp` | About page |
| `/images/experiment-vessel.webp` | Join page |
| `/images/about-inquiry-landscape.webp` | Events page |
| `/images/hero-map-territory.webp` | Starter experiment log cover |
| `/images/og-default.jpg` | Default social share card (1200×630) |
| `/favicon.svg`, `/favicon.ico`, `/icon-*.png`, `/apple-touch-icon.png` | Site icons (dotted route + observation point mark) |

The canonical production URL is `https://www.epistemic-experiments.org`
(configured as the `site` fallback in `astro.config.mjs`; `SITE_URL` env
overrides it). Social/SEO tags live in `src/components/Seo.astro`.

## UI And Accessibility Requirements

Accessibility overrides decorative preference. Future UI changes must preserve
the following decisions.

- Inline prose links remain visibly underlined.
- Current navigation state must use a non-color cue; the active item currently
  uses underline plus weight and color.
- All keyboard-focusable elements must retain an obvious `:focus-visible` ring.
- Standalone navigation and action links should provide touch-friendly targets
  of at least `44px` height where layout allows.
- Primary and secondary buttons must remain visually distinct; outlined
  interactive controls should use `--line-strong`.
- Respect `prefers-reduced-motion`; do not add animation or smooth-motion
  behavior without a reduced-motion fallback.
- Keep a skip-to-content link and semantic landmarks in the shared layout.
- Use real headings in logical order. A page has one `h1`; page sections use
  `h2`; repeated card headings should not compete visually with section headings.

Measured palette requirements already enforced in the design:

| Pairing | Minimum | Current result |
| --- | ---: | ---: |
| Muted text on paper-soft | 4.5:1 | 5.18:1 |
| Muted text on surface | 4.5:1 | 4.90:1 |
| Terracotta eyebrow text on paper | 4.5:1 | 5.47:1 |
| Strong control line on surface | 3:1 | 3.13:1 |
| Blue focus/accent on paper | 3:1 | 7.45:1 |

When changing tokens, remeasure all text and interactive-boundary combinations
instead of estimating by eye.

## Content Model And Publishing Rules

Content schemas are defined in [`src/content.config.ts`](src/content.config.ts).
Do not weaken public visibility filters.

### Events

Events are listed publicly only when all conditions are true:

```ts
event.data.status === "live" &&
event.data.publish_on_site === true &&
Boolean(event.data.luma_url)
```

- Event lifecycle: `draft -> review -> ready_for_luma -> live -> completed -> archived`.
- Luma is manual in v1. Create the Luma event outside the site, then paste the
  public registration URL into the event entry.
- Event and participation links are currently WIP. Do not invent public contact
  channels or test Luma links to make empty states look complete.

### Experiment Logs

Logs are publicly visible only when:

```ts
log.data.status === "published"
```

- Logs are edited summaries, not transcripts.
- Sensitive sessions should use `privacy_level: sensitive` and high-level copy.
- Keep participant details and identifiable personal disclosures out of public logs.

### Resources And Pages

- Resources appear publicly only with `status: published`.
- Editable static page content belongs in `src/content/pages/`.
- Keep editor-facing CMS labels plain and understandable; avoid internal jargon.

## Privacy And Local-Only Data

Privacy is a product requirement, not only a content preference.

- `docs/main.jsonl` is a private local context export and is ignored by Git.
- Do not commit, quote, transform into public content, or expose data from
  `docs/main.jsonl`.
- Do not publish participant names, phone numbers, group links, raw Google Meet
  links, private Luma/admin links, WhatsApp/Discord invites, or personal disclosures.
- Exception: the official community Discord invite
  (`https://discord.gg/nKDVuVTrC`) is approved for public display (used in the
  Kodai log and the contact modal). All other invites remain private.
- If a proposed public summary might identify a participant, leave it out pending review.

## Development And Deployment

Local commands:

```sh
npm install
npm run dev
npm run check
npm run build
npm run preview
```

- If local sandbox restrictions prevent Astro telemetry from writing, run checks
  as `ASTRO_TELEMETRY_DISABLED=1 npm run check` and builds similarly.
- `dist/`, `.astro/`, `node_modules/`, `.vercel/`, `assets_gen/`, and
  `docs/main.jsonl` are local/generated or private and must remain untracked.
- GitHub Actions validates with `npm ci`, `npm run check`, and `npm run build`.
- Vercel owns deployment. This static Astro project requires no Vercel adapter
  and no `vercel.json` unless future functionality changes that constraint.

## Maintenance Checklist

Before shipping future design or content changes:

1. Preserve the warm editorial identity and current component simplicity.
2. Confirm draft/private content cannot enter public queries.
3. Check text and control contrast if any palette or surface changes.
4. Keyboard-tab through new or changed controls and confirm visible focus.
5. Verify touch target sizing for new standalone actions.
6. Optimize newly added public images before tracking them.
7. Run `npm run check` and `npm run build`.

