import { Card, Space, Timeline, Typography } from "antd";
import { eventIconMap } from "../mockData";
import type { TimelineEvent } from "../types";

const { Text } = Typography;

interface TimelinePageProps {
  events: TimelineEvent[];
}

export function TimelinePage({ events }: TimelinePageProps) {
  return (
    <Card className="scroll-page">
      <Timeline
        items={events.map((event: TimelineEvent) => ({
          dot: eventIconMap[event.type],
          children: (
            <Space direction="vertical" size={2}>
              <Text type="secondary">{event.date}</Text>
              <Text strong>
                {event.petName} · {event.title}
              </Text>
              <Text type="secondary">{event.note}</Text>
            </Space>
          ),
        }))}
      />
    </Card>
  );
}
