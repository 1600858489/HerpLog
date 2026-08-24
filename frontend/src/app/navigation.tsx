import {
  CalendarOutlined,
  DashboardOutlined,
  HomeOutlined,
  PlusCircleOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import type { ReactNode } from "react";

export type NavigationKey = "today" | "record" | "pets" | "timeline" | "dashboard";

export interface NavigationItem {
  key: NavigationKey;
  path: string;
  label: string;
  title: string;
  icon: ReactNode;
}

export const navigationItems: readonly NavigationItem[] = [
  { key: "today", path: "/today", label: "今日", title: "今天", icon: <HomeOutlined /> },
  { key: "record", path: "/record", label: "记录", title: "快速记录", icon: <PlusCircleOutlined /> },
  { key: "pets", path: "/pets", label: "宠物", title: "宠物", icon: <TeamOutlined /> },
  { key: "timeline", path: "/timeline", label: "时间线", title: "时间线", icon: <CalendarOutlined /> },
  { key: "dashboard", path: "/dashboard", label: "概览", title: "概览", icon: <DashboardOutlined /> },
];

export function navigationForPath(pathname: string): NavigationItem {
  return navigationItems.find((item) => item.path === pathname) ?? navigationItems[0];
}
