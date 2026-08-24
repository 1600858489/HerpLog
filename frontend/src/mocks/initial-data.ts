import type { Event } from "../entities/event/model";
import type { Pet } from "../entities/pet/model";
import { daysAgo } from "../shared/date";

export const initialPets: readonly Pet[] = [
  {
    id: "pet-1",
    name: "小黑",
    species: "玉米蛇",
    morph: "Anery",
    status: "normal",
    avatarColor: "#466f57",
    careRule: { feedWindowDays: [5, 7], weighEveryDays: 28 },
    bloodline: "玉米蛇 Anery 血统",
    breeder: "本地爬舍",
    hatchDate: "2024-03-12",
    ownerNote: "性格温顺，喜欢躲避在沉木下，喂食时比较积极。",
  },
  {
    id: "pet-2",
    name: "阿黄",
    species: "豹纹守宫",
    morph: "Tangerine",
    status: "observe",
    avatarColor: "#b86e35",
    careRule: { feedWindowDays: [3, 4], weighEveryDays: 14 },
    bloodline: "豹纹守宫 Tangerine 血统",
    breeder: "爬友转让",
    hatchDate: "2023-08-20",
    ownerNote: "最近排泄偏稀，正在观察饮食和湿度变化。",
  },
  {
    id: "pet-3",
    name: "小绿",
    species: "睫角守宫",
    morph: "Harlequin",
    status: "brumation",
    avatarColor: "#557a68",
    careRule: { feedWindowDays: [6, 8], weighEveryDays: 28 },
    bloodline: "睫角守宫 Harlequin 血统",
    breeder: "专业繁殖场",
    hatchDate: "2023-05-05",
    ownerNote: "进入冬化期，活动减少，暂不喂食。",
  },
];

export function createInitialEvents(now = new Date()): Event[] {
  return [
    { id: "event-1", petId: "pet-1", type: "feed", occurredAt: daysAgo(8, now), outcome: "ate", food: "冻鼠", amountGram: 18, note: "" },
    { id: "event-2", petId: "pet-1", type: "weight", occurredAt: daysAgo(14, now), weightGram: 462, note: "" },
    { id: "event-3", petId: "pet-1", type: "weight", occurredAt: daysAgo(42, now), weightGram: 448, note: "" },
    { id: "event-4", petId: "pet-1", type: "shed", occurredAt: daysAgo(18, now), condition: "normal", note: "蜕皮完整" },
    { id: "event-5", petId: "pet-1", type: "photo", occurredAt: daysAgo(3, now), note: "成长记录" },
    { id: "event-6", petId: "pet-2", type: "feed", occurredAt: daysAgo(2, now), outcome: "ate", food: "杜比亚蟑螂", amountGram: 5, note: "" },
    { id: "event-7", petId: "pet-2", type: "weight", occurredAt: daysAgo(21, now), weightGram: 68, note: "" },
    { id: "event-8", petId: "pet-2", type: "poop", occurredAt: daysAgo(1, now), condition: "abnormal", note: "排泄偏稀，继续观察" },
    { id: "event-9", petId: "pet-2", type: "shed", occurredAt: daysAgo(27, now), condition: "normal", note: "" },
    { id: "event-10", petId: "pet-3", type: "feed", occurredAt: daysAgo(10, now), outcome: "ate", food: "果泥", amountGram: 8, note: "冬化前记录" },
    { id: "event-11", petId: "pet-3", type: "weight", occurredAt: daysAgo(32, now), weightGram: 41, note: "" },
    { id: "event-12", petId: "pet-3", type: "photo", occurredAt: daysAgo(5, now), note: "背部花纹变化" },
  ];
}
