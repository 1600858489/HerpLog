import { useNavigate } from "react-router-dom";
import { Button, Card, Empty, List, Space, Tag } from "antd-mobile";
import type { CareTask } from "../../entities/care-task/model";
import { useHerpSnapshot } from "../../app/store-context";

const toneText = { success: "未到时间", warning: "推荐区间", danger: "已超期" } as const;
const toneColor = { success: "success", warning: "warning", danger: "danger" } as const;

/**
 * 今日待办：展示仓库实时推导的护理事项并进入预选记录流程。
 * 用法：页面直接渲染；点击项目会导航到 /record?petId=<id>&type=<type>。
 */
export function TodayFeature() {
  const { careTasks } = useHerpSnapshot();
  const navigate = useNavigate();

  function openRecord(task: CareTask): void {
    navigate(`/record?petId=${task.petId}&type=${task.type}`);
  }

  if (careTasks.length === 0) {
    return <Empty description="今天没有待办事项" />;
  }

  return (
    <Space block direction="vertical" style={{ "--gap": "12px" }}>
      <Card title="今天需要处理">
        <List>
          {careTasks.map((task) => (
            <List.Item
              key={task.id}
              description={task.detail}
              extra={<Tag color={toneColor[task.tone]}>{toneText[task.tone]}</Tag>}
              onClick={() => openRecord(task)}
              clickable
            >
              {task.petName} · {task.title}
            </List.Item>
          ))}
        </List>
      </Card>
      <Button block color="primary" onClick={() => navigate("/record")}>快速记录</Button>
    </Space>
  );
}
