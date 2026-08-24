export type PetStatus = "normal" | "observe" | "brumation";

export interface CareRule {
  feedWindowDays?: readonly [number, number];
  weighEveryDays?: number;
}

export interface Pet {
  id: string;
  name: string;
  species: string;
  morph: string;
  status: PetStatus;
  avatarColor: string;
  careRule: CareRule;
  photoUrl?: string;
  bloodline?: string;
  breeder?: string;
  hatchDate?: string;
  ownerNote?: string;
}

export interface PetSummary extends Pet {
  latestWeightGram?: number;
  nextCareText: string;
}
