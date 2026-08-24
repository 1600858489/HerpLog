import { useSearchParams } from "react-router-dom";
import type { EventType } from "../entities/event/model";
import { RecordFeature } from "../features/record/record-feature";

const eventTypes: readonly EventType[] = ["feed", "weight", "poop", "shed", "photo"];

export function RecordPage() {
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type");
  return <RecordFeature key={`${searchParams.get("petId")}-${type}`} initialPetId={searchParams.get("petId") ?? undefined} initialType={eventTypes.includes(type as EventType) ? type as EventType : undefined} />;
}
