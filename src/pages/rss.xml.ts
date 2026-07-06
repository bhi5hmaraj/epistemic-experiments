import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import { isPublishedLog, newestFirst } from "../lib/content";
import { site, withBase } from "../lib/site";

export async function GET(context: APIContext) {
  const logs = (await getCollection("logs")).filter(isPublishedLog).sort(newestFirst);

  return rss({
    title: `${site.name} — Experiment Logs`,
    description: site.description,
    site: context.site!,
    items: logs.map((log) => ({
      title: log.data.title,
      description: log.data.subtitle,
      pubDate: new Date(`${log.data.date}T00:00:00+05:30`),
      link: withBase(`/logs/${log.data.slug}/`),
    })),
  });
}
