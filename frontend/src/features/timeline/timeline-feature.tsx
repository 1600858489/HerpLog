import { useState } from "react";
import { Empty, List, Selector, Space, Tag } from "antd-mobile";
import { useHerpSnapshot } from "../../app/store-context";
import { eventDescription, eventIcon, eventLabel } from "../../shared/event-presentation";
import { formatEventDate } from "../../shared/date";

/**
 * 时间线：按宠物筛选并倒序展示所有事件。
 * 用法：页面直接渲染；仓库保存事件后列表自动刷新。
 */
export function TimelineFeature() {
  const { pets, events } = useHerpSnapshot();
  const [petId, setPetId] = useState("all");
  const filteredEvents = petId === "all" ? events : events.filter((event) => event.petId === petId);
  const petName = (id: string) => pets.find((pet) => pet.id === id)?.name ?? "未知宠物";

  return (
    <Space block direction="vertical" style={{ "--gap": "12px" }}>
      <Selector
        options={[{ label: "全部", value: "all" }, ...pets.map((pet) => ({ label: pet.name, value: pet.id }))]}
        value={[petId]}
        onChange={(values) => setPetId(values[0] ?? "all")}
      />
      {filteredEvents.length === 0 ? <Empty description="没有匹配的记录" /> : (
        <List>
          {filteredEvents.map((event) => (
            <List.Item
              key={event.id}
              prefix={eventIcon(event.type)}
              description={`${formatEventDate(event.occurredAt)} · ${eventDescription(event)}`}
              extra={event.condition === "abnormal" || event.outcome === "refused" ? <Tag color="danger">异常</Tag> : null}
            >
              {petName(event.petId)} · {eventLabel(event.type)}
            </List.Item>
          ))}
        </List>
      )}
    </Space>
  );
}
