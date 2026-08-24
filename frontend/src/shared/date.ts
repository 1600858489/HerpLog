const dayInMilliseconds = 24 * 60 * 60 * 1000;

export function daysAgo(days: number, now = new Date()): Date {
  const date = new Date(now);
  date.setDate(date.getDate() - days);
  return date;
}

export function formatEventDate(date: Date): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function elapsedDays(from: Date, to: Date): number {
  return Math.floor((to.getTime() - from.getTime()) / dayInMilliseconds);
}
