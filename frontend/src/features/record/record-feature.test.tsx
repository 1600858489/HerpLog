import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AppStoreProvider } from "../../app/store-context";
import { RecordFeature } from "./record-feature";

describe("RecordFeature", () => {
  it("默认喂食可以保存", async () => {
    const user = userEvent.setup();
    render(
      <AppStoreProvider>
        <RecordFeature initialPetId="pet-1" initialType="feed" />
      </AppStoreProvider>,
    );

    await user.click(await screen.findByRole("button", { name: "保存这条记录" }));
    expect(await screen.findByText("已保存")).toBeInTheDocument();
  });
});
