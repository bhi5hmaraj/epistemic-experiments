#!/usr/bin/env node
// Renders local social-share previews for every page on the dev server.
// Usage: npm run dev (in another terminal), then: node scripts/social-preview.mjs
// Writes .social-preview.html and prints its path — open it in a browser.

import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

const BASE = process.env.PREVIEW_BASE ?? "http://localhost:4321";
const ROUTES = [
  "/",
  "/events/",
  "/logs/",
  "/logs/reflections-from-kodai/",
  "/logs/how-we-write-experiment-logs/",
  "/resources/",
  "/about/",
  "/join/",
];

function extractMeta(html) {
  const meta = {};
  const tagRe = /<meta\s+[^>]*>/gi;
  for (const tag of html.match(tagRe) ?? []) {
    const name = tag.match(/(?:name|property)=["']([^"']+)["']/i)?.[1];
    const content = tag.match(/content=["']([^"']*)["']/i)?.[1];
    if (name && content !== undefined) meta[name] = content;
  }
  meta.__title = html.match(/<title>([^<]*)<\/title>/i)?.[1] ?? "";
  meta.__canonical = html.match(/<link\s+rel=["']canonical["']\s+href=["']([^"']+)["']/i)?.[1] ?? "";
  return meta;
}

const esc = (s) => (s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

// Chrome blocks file:// pages from fetching localhost, so inline images as data URIs.
async function toDataUri(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) return "";
    const type = res.headers.get("content-type") ?? "image/jpeg";
    const buf = Buffer.from(await res.arrayBuffer());
    return `data:${type};base64,${buf.toString("base64")}`;
  } catch {
    return "";
  }
}

async function card(route, m) {
  const title = m["og:title"] ?? m.__title;
  const desc = m["og:description"] ?? m.description ?? "";
  const image = m["og:image"] ?? "";
  // Crawlers need absolute URLs; swap the site host for localhost so images render locally.
  const localImage = image ? await toDataUri(image.replace(/^https?:\/\/[^/]+/, BASE)) : "";
  const host = (m.__canonical || m["og:url"] || "").replace(/^https?:\/\//, "").split("/")[0] || "(no canonical)";
  const problems = [];
  if (!m["og:title"]) problems.push("missing og:title");
  if (!m["og:description"]) problems.push("missing og:description");
  if (!image) problems.push("missing og:image");
  else if (!/^https?:\/\//.test(image)) problems.push("og:image is not absolute — crawlers will reject it");
  else if (!localImage) problems.push("og:image path did not resolve on the dev server");
  if (!m["twitter:card"]) problems.push("missing twitter:card");
  if ((desc ?? "").length > 200) problems.push(`description is ${desc.length} chars (WhatsApp/FB truncate ~155)`);
  if (title.length > 70) problems.push(`title is ${title.length} chars (truncates ~60-70)`);

  return `
  <section class="route">
    <h2><code>${esc(route)}</code></h2>
    ${problems.length ? `<ul class="problems">${problems.map((p) => `<li>⚠️ ${esc(p)}</li>`).join("")}</ul>` : `<p class="ok">✓ all social tags present</p>`}
    <div class="cards">
      <figure class="fb">
        <figcaption>WhatsApp / Facebook / LinkedIn</figcaption>
        <div class="fb-card">
          ${localImage ? `<img src="${esc(localImage)}" alt="">` : `<div class="noimg">no og:image</div>`}
          <div class="fb-text">
            <span class="fb-host">${esc(host.toUpperCase())}</span>
            <strong>${esc(title)}</strong>
            <span class="fb-desc">${esc(desc)}</span>
          </div>
        </div>
      </figure>
      <figure class="tw">
        <figcaption>X / Twitter (${esc(m["twitter:card"] ?? "no card")})</figcaption>
        <div class="tw-card">
          ${localImage ? `<img src="${esc(localImage)}" alt="">` : `<div class="noimg">no og:image</div>`}
          <div class="tw-text"><span class="tw-host">${esc(host)}</span><strong>${esc(title)}</strong></div>
        </div>
      </figure>
      <figure class="serp">
        <figcaption>Google result</figcaption>
        <div class="serp-card">
          <span class="serp-url">${esc(m.__canonical || m["og:url"] || "")}</span>
          <a class="serp-title">${esc(m.__title)}</a>
          <span class="serp-desc">${esc(m.description ?? desc)}</span>
        </div>
      </figure>
    </div>
  </section>`;
}

const sections = [];
for (const route of ROUTES) {
  try {
    const res = await fetch(BASE + route);
    sections.push(await card(route, extractMeta(await res.text())));
  } catch (err) {
    sections.push(`<section class="route"><h2><code>${esc(route)}</code></h2><p class="problems">fetch failed: ${esc(String(err))} — is the dev server running?</p></section>`);
  }
}

const out = `<!doctype html><meta charset="utf-8"><title>Social previews — local</title>
<style>
  body { font: 15px/1.45 -apple-system, sans-serif; margin: 2rem auto; max-width: 640px; padding: 0 1rem; background: #f5f5f4; color: #1c1917; }
  .route { margin-bottom: 3rem; }
  h2 { border-bottom: 2px solid #d6d3d1; padding-bottom: 0.3rem; }
  figure { margin: 1.2rem 0; }
  figcaption { font-size: 12px; color: #78716c; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; }
  .problems { color: #b45309; background: #fef3c7; padding: 0.6rem 0.8rem 0.6rem 2rem; border-radius: 8px; }
  .ok { color: #15803d; }
  img { display: block; width: 100%; aspect-ratio: 1.91; object-fit: cover; background: #e7e5e4; }
  .noimg { aspect-ratio: 1.91; display: grid; place-items: center; background: #e7e5e4; color: #a8a29e; }
  .fb-card { border: 1px solid #d6d3d1; background: #f0f2f5; overflow: hidden; }
  .fb-text { padding: 0.6rem 0.75rem; display: grid; gap: 2px; }
  .fb-host { color: #65676b; font-size: 12px; }
  .fb-desc { color: #65676b; font-size: 14px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
  .tw-card { border: 1px solid #cfd9de; border-radius: 16px; overflow: hidden; background: #fff; }
  .tw-text { padding: 0.6rem 0.75rem; display: grid; gap: 2px; }
  .tw-host { color: #536471; font-size: 13px; }
  .serp-card { display: grid; gap: 2px; background: #fff; border: 1px solid #dadce0; border-radius: 8px; padding: 0.8rem 1rem; }
  .serp-url { color: #202124; font-size: 12px; }
  .serp-title { color: #1a0dab; font-size: 19px; cursor: pointer; }
  .serp-title:hover { text-decoration: underline; }
  .serp-desc { color: #4d5156; font-size: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>
<h1>Social previews</h1>
<p>Rendered from <code>${esc(BASE)}</code>. Mock layouts — spacing is approximate, truncation rules are real.</p>
${sections.join("\n")}`;

const outPath = resolve(".social-preview.html");
writeFileSync(outPath, out);
console.log("wrote", outPath);
