export type EventType = "feed" | "weight" | "poop" | "shed" | "photo";
export type FeedOutcome = "ate" | "refused";
export type Condition = "normal" | "abnormal";

export interface Event {
  id: string;
  petId: string;
  type: EventType;
  occurredAt: Date;
  outcome?: FeedOutcome;
  condition?: Condition;
  food?: string;
  amountGram?: number;
  weightGram?: number;
  note: string;
}

export interface EventDraft {
  petId: string;
  type: EventType;
  occurredAt: Date;
  outcome?: FeedOutcome;
  condition?: Condition;
  food?: string;
  amountGram?: number;
  weightGram?: number;
  note: string;
}
