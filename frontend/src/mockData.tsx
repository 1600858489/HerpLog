import {
  CalendarOutlined,
  CameraOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
  FireOutlined,
  HeartOutlined,
  HomeOutlined,
  MedicineBoxOutlined,
  PlusCircleOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import type { ReactNode } from "react";
import type {
  CareTask,
  CareTaskType,
  EventType,
  MetricCard,
  NavItem,
  PetStatus,
  PetSummary,
  TaskTone,
  TimelineEvent,
} from "./types";

export const navItems: NavItem[] = [
  { key: "today", icon: <HomeOutlined />, label: "今日" },
  { key: "record", icon: <PlusCircleOutlined />, label: "记录" },
  { key: "pets", icon: <HeartOutlined />, label: "宠物" },
  { key: "timeline", icon: <ClockCircleOutlined />, label: "时间线" },
  { key: "dashboard", icon: <DashboardOutlined />, label: "概览" },
];

export const metrics: MetricCard[] = [
  { id: "metric-1", label: "今日事项", value: 3, suffix: "项" },
  { id: "metric-2", label: "正在观察", value: 1, suffix: "只" },
  { id: "metric-3", label: "30天记录", value: 28, suffix: "条" },
];

export const careTasks: CareTask[] = [
  {
    id: "task-1",
    petName: "小黑",
    species: "玉米蛇",
    type: "feed",
    title: "建议喂食",
    detail: "默认 18g 冻鼠，距离上次喂食 7 天",
    dueText: "推荐区间",
    tone: "warning",
  },
  {
    id: "task-2",
    petName: "阿黄",
    species: "豹纹守宫",
    type: "mist",
    title: "湿躲避区喷雾",
    detail: "最近湿度偏低，今天建议补水",
    dueText: "今日事项",
    tone: "success",
  },
  {
    id: "task-3",
    petName: "小绿",
    species: "睫角守宫",
    type: "weigh",
    title: "建议称重",
    detail: "上次称重 31 天前，建议更新趋势",
    dueText: "已超期",
    tone: "danger",
  },
];

export const pets: PetSummary[] = [
  {
    id: "pet-1",
    name: "小黑",
    species: "玉米蛇",
    morph: "Anery",
    avatarColor: "#466f57",
    status: "normal",
    weightGram: 462,
    nextCare: "今晚喂食",
    feedProgress: 78,
  },
  {
    id: "pet-2",
    name: "阿黄",
    species: "豹纹守宫",
    morph: "Tangerine",
    avatarColor: "#b86e35",
    status: "observe",
    weightGram: 68,
    nextCare: "喷雾",
    feedProgress: 42,
  },
  {
    id: "pet-3",
    name: "小绿",
    species: "睫角守宫",
    morph: "Harlequin",
    avatarColor: "#557a68",
    status: "normal",
    weightGram: 41,
    nextCare: "称重",
    feedProgress: 64,
  },
];

export const timelineEvents: TimelineEvent[] = [
  {
    id: "event-1",
    date: "今天 08:20",
    petName: "阿黄",
    type: "poop",
    title: "排泄正常",
    note: "颜色与形态正常，已自动关联上次喂食。",
  },
  {
    id: "event-2",
    date: "昨天 21:16",
    petName: "小黑",
    type: "feed",
    title: "喂食准备",
    note: "系统沿用上次默认值：18g 冻鼠。",
  },
  {
    id: "event-3",
    date: "6月24日",
    petName: "小绿",
    type: "photo",
    title: "成长照片",
    note: "新增照片 3 张，记录背部花纹变化。",
  },
  {
    id: "event-4",
    date: "6月20日",
    petName: "小黑",
    type: "weight",
    title: "体重 462g",
    note: "近 30 天体重 +15g，趋势稳定。",
  },
];

export const taskIconMap: Record<CareTaskType, ReactNode> = {
  feed: <FireOutlined />,
  mist: <ThunderboltOutlined />,
  weigh: <DashboardOutlined />,
  medicine: <MedicineBoxOutlined />,
};

export const eventIconMap: Record<EventType, ReactNode> = {
  feed: <FireOutlined />,
  poop: <CheckCircleOutlined />,
  weight: <DashboardOutlined />,
  shed: <HeartOutlined />,
  photo: <CameraOutlined />,
};

export const taskColorMap: Record<TaskTone, string> = {
  success: "green",
  warning: "gold",
  danger: "red",
};

export const petStatusText: Record<PetStatus, string> = {
  normal: "正常",
  observe: "观察中",
  brumation: "冬化",
};
