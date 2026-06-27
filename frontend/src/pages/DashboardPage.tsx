import { Card, Col, Progress, Row, Space, Statistic, Typography } from "antd";
import type { MetricCard } from "../types";

const { Text, Title } = Typography;

interface DashboardPageProps {
  metrics: MetricCard[];
}

export function DashboardPage({ metrics }: DashboardPageProps) {
  return (
    <Space direction="vertical" size={14} className="page-stack dashboard-page">
      <Card>
        <Text type="secondary">最近 30 天</Text>
        <Title level={4}>状态良好</Title>
        <Progress percent={86} status="active" />
      </Card>
      <Row gutter={[12, 12]}>
        {metrics.map((metric: MetricCard) => (
          <Col xs={24} sm={8} key={metric.id}>
            <Card className="metric-card">
              <Statistic title={metric.label} value={metric.value} suffix={metric.suffix} />
            </Card>
          </Col>
        ))}
      </Row>
    </Space>
  );
}
