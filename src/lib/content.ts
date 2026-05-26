import type { CollectionEntry } from "astro:content";

export function isPublicEvent(event: CollectionEntry<"events">): boolean {
  return (
    event.data.status === "live" &&
    event.data.publish_on_site === true &&
    Boolean(event.data.luma_url)
  );
}

export function isPublishedLog(log: CollectionEntry<"logs">): boolean {
  return log.data.status === "published";
}

export function newestFirst<T extends { data: { date: string } }>(a: T, b: T) {
  return b.data.date.localeCompare(a.data.date);
}
