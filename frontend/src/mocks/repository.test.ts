import { describe, expect, it, vi } from "vitest";
import { createHerpRepository } from "./repository";

describe("HerpRepository", () => {
  it("保存喂食后移除对应的喂食待办并通知订阅者", () => {
    const repository = createHerpRepository();
    const before = repository.getCareTasks().find((task) => task.type === "feed");
    expect(before).toBeDefined();
    const listener = vi.fn();
    repository.subscribe(listener);

    repository.saveEvent({
      petId: before!.petId,
      type: "feed",
      occurredAt: new Date(),
      outcome: "ate",
      food: "冻鼠",
      amountGram: 18,
      note: "",
    });

    expect(listener).toHaveBeenCalledOnce();
    expect(repository.getCareTasks().some((task) => task.petId === before!.petId && task.type === "feed")).toBe(false);
    expect(repository.getEvents()[0]).toMatchObject({ petId: before!.petId, type: "feed", outcome: "ate" });
  });

  it("冬化中的宠物不产生喂食待办", () => {
    const repository = createHerpRepository();
    expect(repository.getCareTasks().some((task) => task.petStatus === "brumation" && task.type === "feed")).toBe(false);
  });

  it("将拒食、异常排泄和异常蜕皮计入近 30 天异常数", () => {
    const repository = createHerpRepository();
    expect(repository.getDashboardSummary().abnormalEventCount).toBeGreaterThan(0);
  });
});
