import type { ReactNode } from "react";

export type PageKey = "today" | "record" | "pets" | "timeline" | "dashboard";
export type CareTaskType = "feed" | "mist" | "weigh" | "medicine";
export type TaskTone = "success" | "warning" | "danger";
export type PetStatus = "normal" | "observe" | "brumation";
export type EventType = "feed" | "poop" | "weight" | "shed" | "photo";

export interface NavItem {
  key: PageKey;
  label: string;
  icon: ReactNode;
}

export interface CareTask {
  id: string;
  petName: string;
  species: string;
  type: CareTaskType;
  title: string;
  detail: string;
  dueText: string;
  tone: TaskTone;
}

export interface PetSummary {
  id: string;
  name: string;
  species: string;
  morph: string;
  avatarColor: string;
  status: PetStatus;
  weightGram: number;
  nextCare: string;
  feedProgress: number;
}

export interface TimelineEvent {
  id: string;
  date: string;
  petName: string;
  type: EventType;
  title: string;
  note: string;
}

export interface MetricCard {
  id: string;
  label: string;
  value: number;
  suffix: string;
}
