import { Avatar, Card, Flex, Progress, Space, Tag, Typography } from "antd";
import { petStatusText } from "../mockData";
import type { PetSummary } from "../types";

const { Text } = Typography;

interface PetCardProps {
  pet: PetSummary;
}

export function PetCard({ pet }: PetCardProps) {
  return (
    <Card className="pet-card">
      <Flex gap={12} align="flex-start">
        <Avatar size={44} style={{ backgroundColor: pet.avatarColor }}>
          {pet.name.slice(0, 1)}
        </Avatar>
        <Space direction="vertical" size={8} className="full-width">
          <Flex justify="space-between" align="center" gap={10}>
            <Text strong>{pet.name}</Text>
            <Tag>{petStatusText[pet.status]}</Tag>
          </Flex>
          <Text type="secondary">
            {pet.species} · {pet.morph} · {pet.weightGram}g
          </Text>
          <Progress percent={pet.feedProgress} size="small" />
          <Text type="secondary">下一步：{pet.nextCare}</Text>
        </Space>
      </Flex>
    </Card>
  );
}
