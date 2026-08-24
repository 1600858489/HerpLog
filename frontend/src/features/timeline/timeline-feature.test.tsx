import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AppStoreProvider } from "../../app/store-context";
import { TimelineFeature } from "./timeline-feature";

describe("TimelineFeature", () => {
  it("可按宠物筛选时间线", async () => {
    const user = userEvent.setup();
    render(
      <AppStoreProvider>
        <TimelineFeature />
      </AppStoreProvider>,
    );

    await user.click(await screen.findByText("小黑"));
    expect(screen.queryByText(/阿黄 ·/)).not.toBeInTheDocument();
  });
});
