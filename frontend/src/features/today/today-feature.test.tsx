import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AppStoreProvider } from "../../app/store-context";
import { TodayFeature } from "./today-feature";

describe("TodayFeature", () => {
  it("点击待办时带着宠物和事件类型跳转到记录页", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/today"]}>
        <AppStoreProvider>
          <Routes>
            <Route path="/today" element={<TodayFeature />} />
            <Route path="/record" element={<div>记录页</div>} />
          </Routes>
        </AppStoreProvider>
      </MemoryRouter>,
    );

    await user.click(await screen.findByText("小黑 · 建议喂食"));
    expect(screen.getByText("记录页")).toBeInTheDocument();
  });
});
