import type { CareTask } from "../entities/care-task/model";
import type { DashboardSummary } from "../entities/dashboard/model";
import type { Event, EventDraft, EventType } from "../entities/event/model";
import type { PetSummary } from "../entities/pet/model";
import { deriveCareTasks, deriveDashboardSummary, derivePetSummaries, getLatestEvent } from "./derive";
import { createInitialEvents, initialPets } from "./initial-data";

export interface HerpRepository {
  getPets(): readonly PetSummary[];
  getEvents(petId?: string): readonly Event[];
  getCareTasks(): readonly CareTask[];
  getDashboardSummary(): DashboardSummary;
  getLatestEvent(petId: string, type: EventType): Event | undefined;
  getVersion(): number;
  saveEvent(draft: EventDraft): Event;
  subscribe(listener: () => void): () => void;
}

function copyEvent(event: Event): Event {
  return { ...event, occurredAt: new Date(event.occurredAt) };
}

function createEventId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `evt-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function createHerpRepository(now: () => Date = () => new Date()): HerpRepository {
  const startedAt = now();
  const pets = initialPets.map((pet) => ({ ...pet, careRule: { ...pet.careRule } }));
  const events = createInitialEvents(startedAt).map(copyEvent);
  const listeners = new Set<() => void>();
  let version = 0;

  function sortedEvents(petId?: string): Event[] {
    return events
      .filter((event) => !petId || event.petId === petId)
      .sort((left, right) => right.occurredAt.getTime() - left.occurredAt.getTime())
      .map(copyEvent);
  }

  function notify(): void {
    listeners.forEach((listener) => listener());
  }

  return {
    getPets: () => derivePetSummaries(pets, events, now()),
    getEvents: (petId) => sortedEvents(petId),
    getCareTasks: () => deriveCareTasks(pets, events, now()),
    getDashboardSummary: () => deriveDashboardSummary(events, pets, now()),
    getLatestEvent: (petId, type) => getLatestEvent(events, petId, type),
    getVersion: () => version,
    saveEvent: (draft) => {
      const event: Event = { ...draft, id: createEventId(), occurredAt: new Date(draft.occurredAt) };
      events.push(event);
      events.sort((left, right) => right.occurredAt.getTime() - left.occurredAt.getTime());
      version += 1;
      notify();
      return copyEvent(event);
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
