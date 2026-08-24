export interface PetInsight {
  petId: string;
  petName: string;
  status: "normal" | "observe" | "brumation";
  headline: string;
  detail: string;
  tone: "success" | "warning" | "danger";
}

export interface DashboardSummary {
  recordCount: number;
  feedCount: number;
  weightChangeGram: number;
  abnormalEventCount: number;
  healthText: string;
  petInsights: PetInsight[];
}
