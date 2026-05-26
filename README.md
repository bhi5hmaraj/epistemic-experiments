# Epistemic Experiments

A content-first Astro website for public events, experiment logs, and annotated
resources. Pages CMS edits Markdown files in GitHub; Luma remains the manual
registration system for events.

## Site Workflow

```txt
Edit content in Pages CMS or Markdown
  -> review privacy and publication fields
  -> open/merge changes into main
  -> GitHub Actions validates and builds
  -> Vercel builds and deploys the static site
```

Events have an additional manual Luma step:

```txt
Draft event -> review copy -> create event in Luma -> paste Luma URL
  -> set event live and publish_on_site -> merge/deploy
```

## Local Development

Prerequisites:

- Node.js 22 or newer.
- npm.

Set up and run the site:

```sh
npm install
npm run dev
```

Astro prints the local preview URL, normally `http://localhost:4321/`.

Build and serve the production version locally:

```sh
npm run check
npm run build
npm run preview
```

`npm run build` writes static output to `dist/`. Astro normally serves the
production preview at `http://localhost:4321/`.

Before submitting content or code changes, run at minimum:

```sh
npm run check
npm run build
```

Useful commands:

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the local development server with live reload. |
| `npm run check` | Validate Astro templates, TypeScript, and content schemas. |
| `npm run build` | Generate the production static site in `dist/`. |
| `npm run preview` | Serve the last production build locally. |

If Astro telemetry cannot write its config directory in a restricted environment,
run commands with `ASTRO_TELEMETRY_DISABLED=1`.

## Content Locations

Content is stored as Markdown with YAML frontmatter and validated by
[`src/content.config.ts`](src/content.config.ts).

| Content | Directory | Public rule |
| --- | --- | --- |
| Events | `src/content/events/` | `status: live`, `publish_on_site: true`, and a non-empty `luma_url`. |
| Experiment logs | `src/content/logs/` | `status: published`. |
| Resources | `src/content/resources/` | `status: published`. |
| Editable pages | `src/content/pages/` | Rendered directly on their route. |

Public routes are `/`, `/events`, `/logs`, `/resources`, `/about`, and `/join`.

## Editing With Pages CMS

[Pages CMS](https://pagescms.org/) reads [`.pages.yml`](.pages.yml) from this
repository. Once the repository is connected in Pages CMS, editors can manage:

- Events.
- Experiment logs.
- Resources.
- About and Join page copy.
- Images stored in `public/images/`.

Recommended editor flow:

1. Create or edit content in Pages CMS.
2. Leave new events and logs in draft or review state until copy and privacy have been checked.
3. Confirm that no private links, participant details, or identifiable disclosures are included.
4. Publish through the relevant status field only when the content is ready for the public site.
5. Merge the resulting repository change into `main` to trigger a Vercel production deployment.

Technical maintainers can make the same edits directly in `src/content/` and run
the local checks before pushing.

## Publishing An Event

Luma manages registration and live event logistics. The website does not create
Luma events or expose meeting links.

Event lifecycle:

```txt
draft -> review -> ready_for_luma -> live -> completed -> archived
```

To publish an upcoming event:

1. Create an event entry with a title, summary, date, time, format, and topics.
2. Review the public copy and any privacy implications.
3. Set `status` to `ready_for_luma`.
4. Create the registration event manually in Luma.
5. Paste the public Luma registration URL into `luma_url`.
6. Set `status` to `live`.
7. Set `publish_on_site` to `true`.
8. Merge and deploy the change.

The website intentionally hides an event unless all public conditions are met.
Never place a raw Meet, WhatsApp, Discord, or private community invite link in an
event entry.

After an event happens, set its status to `completed` and decide whether it
should have a public experiment log.

## Publishing An Experiment Log

Experiment logs capture useful public learning, not transcripts.

Suggested structure:

```md
## Question explored

## What happened

## Key takeaways

## Interesting disagreements or tensions

## Open questions

## Resources shared

## Next experiment
```

Log publishing flow:

1. Create a log as `draft` and, where applicable, set `related_event`.
2. Write a high-level summary that stands without naming participants or exposing private conversation.
3. Set `privacy_level: sensitive` if the session involved personal or sensitive material.
4. Review the log before changing `status` to `published`.
5. Merge and deploy.

Sensitive logs display a notice that participant details and personal questions
have intentionally been omitted.

## Images

Site-delivered media belongs in `public/images/` and can be uploaded through
Pages CMS. Prefer optimized `.webp` files for illustrations and hero images.

`assets_gen/` is reserved for local high-resolution source images and is ignored
by Git. `docs/main.jsonl` is also ignored and must not be committed.

To produce a smaller WebP copy from a local source image with ImageMagick:

```sh
magick "assets_gen/source-image.png" -resize "1440x>" -strip -quality 80 public/images/site-image.webp
```

Then reference the public path in content frontmatter:

```yaml
cover_image: "/images/site-image.webp"
```

## Privacy Rules

Treat the public site as an edited archive, not a mirror of community discussion.

- Do not publish chat exports or contact details.
- Do not publish raw video-call or private group invite links.
- Do not attribute participant questions or personal disclosures without explicit approval.
- Use high-level summaries for sensitive sessions.
- When unsure whether something should be public, omit it until reviewed.

## Validation

The validation workflow in [`.github/workflows/validate.yml`](.github/workflows/validate.yml)
runs on pull requests and pushes to `main`:

```txt
npm ci -> npm run check -> npm run build
```

## Deploying With Vercel

This is a static Astro site. Vercel supports static Astro deployments without an
Astro adapter or a `vercel.json` file.

### Recommended: Git Integration

1. Push this repository to GitHub.
2. In Vercel, create a new project and import the GitHub repository.
3. Confirm that Vercel detects **Astro** as the framework preset.
4. Confirm the build settings if Vercel prompts for them:

   ```txt
   Install Command: npm install
   Build Command: npm run build
   Output Directory: dist
   ```

5. Deploy the project.
6. Set `main` as the production branch if it is not already selected.

With Git integration:

- Changes pushed to branches or pull requests receive Vercel preview deployments.
- Changes merged into `main` receive a production deployment.
- The GitHub validation workflow still checks the build independently before or during review.

### Optional: Vercel CLI

Install the CLI and deploy a preview build from the repository root:

```sh
npm install --global vercel
vercel
```

Deploy the current revision to production:

```sh
vercel --prod
```

The CLI creates local Vercel project metadata under `.vercel/`, which is already
ignored by Git.

## Implementation Reference

The first-version design and product constraints are documented in
[`docs/ee_website_implementation_design_doc.md`](docs/ee_website_implementation_design_doc.md).
