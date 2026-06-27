import {
  Button,
  Card,
  Col,
  InputNumber,
  Radio,
  Row,
  Segmented,
  Select,
  Space,
  Typography,
} from "antd";
import { CameraOutlined, DashboardOutlined, FireOutlined, SaveOutlined } from "@ant-design/icons";

const { Text, Title } = Typography;

export function RecordPage() {
  return (
    <Space direction="vertical" size={14} className="page-stack record-page">
      <Card className="record-panel">
        <Space direction="vertical" size={14} className="full-width">
          <div>
            <Text type="secondary">动作流</Text>
            <Title level={4}>3 步完成今日记录</Title>
          </div>
          <Segmented block options={["喂食", "体重", "照片"]} />
          <Select
            className="full-width"
            defaultValue="pet-1"
            options={[
              { value: "pet-1", label: "小黑 · 玉米蛇" },
              { value: "pet-2", label: "阿黄 · 豹纹守宫" },
              { value: "pet-3", label: "小绿 · 睫角守宫" },
            ]}
          />
          <Radio.Group
            block
            defaultValue="ate"
            optionType="button"
            options={[
              { value: "ate", label: "吃了" },
              { value: "refused", label: "拒食" },
            ]}
          />
          <Row gutter={12}>
            <Col span={12}>
              <InputNumber addonAfter="g" className="full-width" defaultValue={18} min={0} />
            </Col>
            <Col span={12}>
              <Select
                className="full-width"
                defaultValue="mouse"
                options={[
                  { value: "mouse", label: "冻鼠" },
                  { value: "insect", label: "昆虫" },
                ]}
              />
            </Col>
          </Row>
          <Button block type="primary" size="large" icon={<SaveOutlined />}>
            保存记录
          </Button>
        </Space>
      </Card>

      <Row gutter={[12, 12]}>
        <Col xs={8}>
          <Button block icon={<FireOutlined />}>
            喂食
          </Button>
        </Col>
        <Col xs={8}>
          <Button block icon={<DashboardOutlined />}>
            称重
          </Button>
        </Col>
        <Col xs={8}>
          <Button block icon={<CameraOutlined />}>
            照片
          </Button>
        </Col>
      </Row>
    </Space>
  );
}
