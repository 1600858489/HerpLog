import { Avatar, Button, Card, Flex, Space, Tag, Typography } from "antd";
import { taskColorMap, taskIconMap } from "../mockData";
import type { CareTask } from "../types";

const { Text } = Typography;

interface TaskCardProps {
  task: CareTask;
  compact?: boolean;
}

export function TaskCard({ task, compact = false }: TaskCardProps) {
  return (
    <Card className={compact ? "task-card compact" : "task-card"}>
      <Flex align="flex-start" gap={12}>
        <Avatar
          icon={taskIconMap[task.type]}
          style={{ backgroundColor: task.tone === "danger" ? "#cf4f3f" : "#3f7d58" }}
        />
        <Space direction="vertical" size={6} className="full-width">
          <Flex align="center" justify="space-between" gap={8}>
            <Text strong>{task.petName}</Text>
            <Tag color={taskColorMap[task.tone]}>{task.dueText}</Tag>
          </Flex>
          <Text>{task.title}</Text>
          <Text type="secondary">{task.detail}</Text>
          {!compact && (
            <Button block type="primary">
              完成
            </Button>
          )}
        </Space>
      </Flex>
    </Card>
  );
}
