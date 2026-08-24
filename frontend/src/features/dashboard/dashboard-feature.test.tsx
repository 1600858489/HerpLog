import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AppStoreProvider } from "../../app/store-context";
import { DashboardFeature } from "./dashboard-feature";

describe("DashboardFeature", () => {
  it("显示仓库推导出的近 30 天统计", () => {
    render(
      <AppStoreProvider>
        <DashboardFeature />
      </AppStoreProvider>,
    );

    expect(screen.getByText("最近 30 天")).toBeInTheDocument();
    expect(screen.getByText("记录")).toBeInTheDocument();
    expect(screen.getByText("喂食")).toBeInTheDocument();
    expect(screen.getByText("异常")).toBeInTheDocument();
  });
});
