import type { Event } from "../entities/event/model";

export function isAbnormalEvent(event: Event): boolean {
  return event.outcome === "refused" || event.condition === "abnormal";
}
