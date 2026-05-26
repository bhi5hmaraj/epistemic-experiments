export const site = {
  name: "Epistemic Experiments",
  description: "A small community testing better ways to think, talk, and learn together.",
};

export function withBase(path: string): string {
  const prefix = import.meta.env.BASE_URL.endsWith("/")
    ? import.meta.env.BASE_URL
    : `${import.meta.env.BASE_URL}/`;

  return `${prefix}${path.replace(/^\/+/, "")}`;
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "Asia/Kolkata",
  }).format(new Date(`${date}T00:00:00+05:30`));
}
