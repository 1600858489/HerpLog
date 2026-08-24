import {
  CameraOutlined,
  CheckCircleOutlined,
  FireOutlined,
  RiseOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import type { ReactNode } from "react";
import type { Event, EventType } from "../entities/event/model";

export function eventLabel(type: EventType): string {
  return { feed: "喂食", weight: "体重", poop: "排泄", shed: "蜕皮", photo: "照片" }[type];
}

export function eventIcon(type: EventType): ReactNode {
  return {
    feed: <FireOutlined />,
    weight: <RiseOutlined />,
    poop: <CheckCircleOutlined />,
    shed: <ThunderboltOutlined />,
    photo: <CameraOutlined />,
  }[type];
}

export function eventDescription(event: Event): string {
  if (event.type === "feed") {
    return `${event.outcome === "refused" ? "拒食" : "吃了"}${event.food ? ` · ${event.food}` : ""}${event.amountGram ? ` · ${event.amountGram}g` : ""}`;
  }
  if (event.type === "weight") return `体重 ${event.weightGram ?? "-"}g`;
  if (event.type === "poop") return event.condition === "abnormal" ? "排泄异常" : "排泄正常";
  if (event.type === "shed") return event.condition === "abnormal" ? "蜕皮异常" : "蜕皮成功";
  return event.note || "新增照片记录";
}
