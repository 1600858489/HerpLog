import type { EventType } from "../event/model";
import type { PetStatus } from "../pet/model";

export type CareTaskTone = "success" | "warning" | "danger";

export interface CareTask {
  id: string;
  petId: string;
  petName: string;
  petStatus: PetStatus;
  type: Extract<EventType, "feed" | "weight">;
  title: string;
  detail: string;
  tone: CareTaskTone;
}
