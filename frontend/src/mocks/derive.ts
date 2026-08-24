import type { CareTask, CareTaskTone } from "../entities/care-task/model";
import type { DashboardSummary } from "../entities/dashboard/model";
import type { Event, EventType } from "../entities/event/model";
import type { Pet, PetSummary } from "../entities/pet/model";
import { elapsedDays } from "../shared/date";
import { isAbnormalEvent } from "../shared/event-rules";

function sortNewestFirst(events: readonly Event[]): Event[] {
  return [...events].sort((left, right) => right.occurredAt.getTime() - left.occurredAt.getTime());
}

export function getLatestEvent(events: readonly Event[], petId: string, type: EventType): Event | undefined {
  return sortNewestFirst(events).find((event) => event.petId === petId && event.type === type);
}

function careTone(days: number, window: readonly [number, number]): CareTaskTone {
  if (days < window[0]) return "success";
  if (days <= window[1]) return "warning";
  return "danger";
}

export function deriveCareTasks(pets: readonly Pet[], events: readonly Event[], now: Date): CareTask[] {
  const tasks: CareTask[] = [];

  for (const pet of pets) {
    const { careRule } = pet;
    if (pet.status !== "brumation" && careRule.feedWindowDays) {
      const lastFeed = getLatestEvent(events, pet.id, "feed");
      const days = lastFeed ? elapsedDays(lastFeed.occurredAt, now) : careRule.feedWindowDays[1] + 1;
      const tone = careTone(days, careRule.feedWindowDays);
      if (tone !== "success") {
        tasks.push({
          id: `${pet.id}-feed`,
          petId: pet.id,
          petName: pet.name,
          petStatus: pet.status,
          type: "feed",
          title: "建议喂食",
          detail: lastFeed ? `距离上次喂食 ${days} 天` : "尚未记录喂食",
          tone,
        });
      }
    }

    if (careRule.weighEveryDays) {
      const lastWeight = getLatestEvent(events, pet.id, "weight");
      const days = lastWeight ? elapsedDays(lastWeight.occurredAt, now) : careRule.weighEveryDays;
      if (days >= careRule.weighEveryDays) {
        tasks.push({
          id: `${pet.id}-weight`,
          petId: pet.id,
          petName: pet.name,
          petStatus: pet.status,
          type: "weight",
          title: "建议称重",
          detail: lastWeight ? `上次称重 ${days} 天前` : "尚未记录体重",
          tone: days > careRule.weighEveryDays ? "danger" : "warning",
        });
      }
    }
  }

  const weight = { danger: 0, warning: 1, success: 2 } as const;
  return tasks.sort((left, right) => weight[left.tone] - weight[right.tone]);
}

export function derivePetSummaries(pets: readonly Pet[], events: readonly Event[], now: Date): PetSummary[] {
  const tasks = deriveCareTasks(pets, events, now);
  return pets.map((pet) => {
    const latestWeight = getLatestEvent(events, pet.id, "weight");
    const task = tasks.find((candidate) => candidate.petId === pet.id);
    return {
      ...pet,
      latestWeightGram: latestWeight?.weightGram,
      nextCareText: task ? task.title : pet.status === "brumation" ? "冬化中，暂停喂食提醒" : "暂无待办",
    };
  });
}

export function deriveDashboardSummary(
  events: readonly Event[],
  pets: readonly Pet[],
  now: Date,
): DashboardSummary {
  const threshold = new Date(now);
  threshold.setDate(threshold.getDate() - 30);
  const recentEvents = events.filter((event) => event.occurredAt >= threshold && event.occurredAt <= now);
  const weightChangeGram = pets.reduce((total, pet) => {
    const weights = recentEvents
      .filter((event) => event.petId === pet.id && event.type === "weight" && event.weightGram !== undefined)
      .sort((left, right) => left.occurredAt.getTime() - right.occurredAt.getTime());
    if (weights.length < 2) return total;
    return total + weights[weights.length - 1].weightGram! - weights[0].weightGram!;
  }, 0);
  const abnormalEventCount = recentEvents.filter(isAbnormalEvent).length;
  const tasks = deriveCareTasks(pets, events, now);
  const petInsights = pets.map((pet) => {
    const petEvents = recentEvents.filter((event) => event.petId === pet.id);
    const abnormal = petEvents.filter(isAbnormalEvent).length;
    const task = tasks.find((candidate) => candidate.petId === pet.id);
    if (abnormal > 0) {
      return { petId: pet.id, petName: pet.name, status: pet.status, headline: "需要留意", detail: `${abnormal} 条异常记录，建议查看时间线`, tone: "danger" as const };
    }
    if (task) {
      return { petId: pet.id, petName: pet.name, status: pet.status, headline: task.title, detail: task.detail, tone: task.tone };
    }
    return { petId: pet.id, petName: pet.name, status: pet.status, headline: "状态平稳", detail: pet.status === "brumation" ? "冬化中，保持环境稳定" : "近期没有需要立即处理的事项", tone: "success" as const };
  });

  return {
    recordCount: recentEvents.length,
    feedCount: recentEvents.filter((event) => event.type === "feed").length,
    weightChangeGram,
    abnormalEventCount,
    healthText: abnormalEventCount === 0 ? "整体状态平稳" : "有宠物需要关注",
    petInsights,
  };
}
