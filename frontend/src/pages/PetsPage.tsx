import { Space } from "antd";
import { PetCard } from "../components/PetCard";
import type { PetSummary } from "../types";

interface PetsPageProps {
  pets: PetSummary[];
}

export function PetsPage({ pets }: PetsPageProps) {
  return (
    <Space direction="vertical" size={12} className="page-stack scroll-page">
      {pets.map((pet: PetSummary) => (
        <PetCard key={pet.id} pet={pet} />
      ))}
    </Space>
  );
}
