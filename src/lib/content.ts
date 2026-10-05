import type { CollectionEntry } from "astro:content";

export interface RegistrationLink {
  url: string;
  label: string;
}

/** Where visitors sign up: Luma when the event has it, otherwise the editor's own form link. */
export function registrationLink(event: CollectionEntry<"events">): RegistrationLink | undefined {
  if (event.data.luma_url) return { url: event.data.luma_url, label: "RSVP on Luma" };
  if (event.data.registration_url) {
    return { url: event.data.registration_url, label: event.data.registration_label };
  }
  return undefined;
}

export function isPublicEvent(event: CollectionEntry<"events">): boolean {
  return (
    event.data.status === "live" &&
    event.data.publish_on_site === true &&
    Boolean(registrationLink(event))
  );
}

/** A public event with body text gets a page of its own at /events/<slug>/. */
export function hasEventPage(event: CollectionEntry<"events">): boolean {
  return isPublicEvent(event) && Boolean(event.body?.trim());
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
    Boolean(registrationLink(event)) &&
    (event.data.status === "live" || event.data.status === "completed");

  return isPublicArchiveEvent && (event.data.status === "completed" || eventHasEnded(event, now));
}

export function isPublishedLog(log: CollectionEntry<"logs">): boolean {
  return log.data.status === "published";
}

export function newestFirst<T extends { data: { date: string } }>(a: T, b: T) {
  return b.data.date.localeCompare(a.data.date);
}
