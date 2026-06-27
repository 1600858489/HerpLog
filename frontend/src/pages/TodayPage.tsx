import { Button, Card, Col, Row, Space, Statistic, Typography } from "antd";
import { PlusCircleOutlined } from "@ant-design/icons";
import { TaskCard } from "../components/TaskCard";
import type { CareTask, MetricCard } from "../types";

const { Text, Title } = Typography;

interface TodayPageProps {
  tasks: CareTask[];
  metrics: MetricCard[];
  onRecord: () => void;
}

export function TodayPage({ tasks, metrics, onRecord }: TodayPageProps) {
  const primaryTask = tasks[0];

  return (
    <Space direction="vertical" size={16} className="page-stack today-page">
      <Row gutter={[12, 12]}>
        {metrics.map((metric: MetricCard) => (
          <Col xs={8} sm={8} md={8} key={metric.id}>
            <Card className="metric-card">
              <Statistic title={metric.label} value={metric.value} suffix={metric.suffix} />
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="focus-card">
        <Space direction="vertical" size={12} className="full-width">
          <Text type="secondary">当前最需要处理</Text>
          <Title level={4}>{primaryTask.petName} · {primaryTask.title}</Title>
          <Text>{primaryTask.detail}</Text>
          <Button block type="primary" icon={<PlusCircleOutlined />} onClick={onRecord}>
            进入快速记录
          </Button>
        </Space>
      </Card>

      <div className="task-preview-grid">
        {tasks.slice(1).map((task: CareTask) => (
          <TaskCard compact key={task.id} task={task} />
        ))}
      </div>
    </Space>
  );
}
