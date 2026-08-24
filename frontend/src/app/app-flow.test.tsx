import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { App } from "./App";

describe("核心业务流", () => {
  it("从今日进入预选记录，保存后刷新时间线和概览", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/today"]}>
        <App />
      </MemoryRouter>,
    );

    await user.click(await screen.findByText("小黑 · 建议喂食"));
    await user.click(await screen.findByRole("button", { name: "保存这条记录" }));

    expect(await screen.findByText("已保存")).toBeInTheDocument();
    expect(screen.queryByText("小黑 · 建议喂食")).not.toBeInTheDocument();

    await user.click(screen.getByText("时间线"));
    expect((await screen.findAllByText(/吃了 · 冻鼠 · 18g/)).length).toBeGreaterThan(1);

    await user.click(screen.getByText("概览"));
    expect(await screen.findByText("最近 30 天")).toBeInTheDocument();
  });
});
