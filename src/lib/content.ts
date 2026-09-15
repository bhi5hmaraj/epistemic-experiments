import type { CollectionEntry } from "astro:content";

export function isPublicEvent(event: CollectionEntry<"events">): boolean {
  return (
    event.data.status === "live" &&
    event.data.publish_on_site === true &&
    Boolean(event.data.luma_url)
  );
}

function eventHasEnded(event: CollectionEntry<"events">, now: Date): boolean {
  if (!event.data.end_at) return false;

  const endTime = Date.parse(event.data.end_at);
  return Number.isFinite(endTime) && endTime <= now.getTime();
}

/** Events that are still open for registration. */
export function isUpcomingEvent(
  event: CollectionEntry<"events">,
  now = new Date(),
): boolean {
  return isPublicEvent(event) && !eventHasEnded(event, now);
}

/**
 * Public events remain part of the archive after they end. Editors may also
 * explicitly mark an event completed when it has no exact end time.
 */
export function isPastEvent(
  event: CollectionEntry<"events">,
  now = new Date(),
): boolean {
  const isPublicArchiveEvent =
    event.data.publish_on_site === true &&
    Boolean(event.data.luma_url) &&
    (event.data.status === "live" || event.data.status === "completed");

  return isPublicArchiveEvent && (event.data.status === "completed" || eventHasEnded(event, now));
}

export function isPublishedLog(log: CollectionEntry<"logs">): boolean {
  return log.data.status === "published";
}

export function newestFirst<T extends { data: { date: string } }>(a: T, b: T) {
  return b.data.date.localeCompare(a.data.date);
}
