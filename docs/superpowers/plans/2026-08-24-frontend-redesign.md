# HerpLog 前端完全重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个移动优先、双端响应式、可用 Mock 数据完整联动的 HerpLog 前端原型。

**Architecture:** React 应用通过 `AppStoreProvider` 访问唯一的内存 Mock 仓库；仓库保存 Event 后重新推导宠物摘要、今日待办和概览。页面只负责组装 feature，feature 使用 antd-mobile/antd 的组件进行展示与交互；应用壳层在 992px 断点切换移动导航与桌面侧栏，但不复制业务页面或数据流。

**Tech Stack:** React 18、TypeScript、Vite 5、antd 6、antd-mobile 5、React Router、Vitest、Testing Library。

## Global Constraints

- 保留 React 18、TypeScript、Vite，新增 `antd-mobile` 与 `react-router-dom`；不替换现有 antd。
- 手机端小于 768px，平板端 768px 至 991px，PC 端不小于 992px。
- 基础 UI 必须来自 antd 或 antd-mobile；不得手写 Button、Card、TabBar、NavBar、Dialog、Toast、Form 或类似基础控件。
- CSS 仅可处理应用级布局、断点、内容宽度、间距和安全区，不得重造组件库视觉样式。
- 使用相对当前日期构造初始 Mock 时间；刷新页面必须恢复初始 Mock 数据。
- Mock 仓库是唯一可变数据源；页面和展示组件不得直接改写数据。
- 保存 Event 必须即时联动今日、宠物、时间线与概览。
- 本次不实现后端 API、持久化、登录、真实图片上传、完整 Care Plan 编辑、日历或复杂趋势图。
- 不创建 git commit，除非用户在执行阶段明确要求。

---

## 目标文件结构

```text
frontend/
├── package.json                                  修改：增加运行、类型检查、测试脚本和依赖
├── vite.config.ts                                修改：加入 Vitest 配置
├── src/
│   ├── main.tsx                                  修改：加载两套组件库样式并挂载路由应用
│   ├── app/
│   │   ├── App.tsx                               新建：Provider、Router、双端应用壳层与路由出口
│   │   ├── app-shell.tsx                         新建：移动 NavBar/TabBar 和桌面 Layout/Sider/Menu
│   │   ├── navigation.tsx                        新建：导航定义、页面标题与 Ant 图标映射
│   │   └── store-context.tsx                     新建：仓库 React Context 与 useSyncExternalStore 桥接
│   ├── entities/
│   │   ├── pet/model.ts                          新建：Pet、PetStatus、CareRule 类型
│   │   ├── event/model.ts                        新建：Event、EventDraft、EventType 类型
│   │   ├── care-task/model.ts                    新建：CareTask、CareTaskTone 类型
│   │   └── dashboard/model.ts                    新建：DashboardSummary 类型
│   ├── mocks/
│   │   ├── initial-data.ts                       新建：相对日期的 Pet/Event 初始数据
│   │   ├── derive.ts                             新建：派生宠物、待办和概览的纯函数
│   │   ├── repository.ts                         新建：内存仓库接口及实现
│   │   └── repository.test.ts                    新建：仓库、规则和联动单元测试
│   ├── shared/
│   │   ├── date.ts                               新建：日期格式化和相对日期辅助函数
│   │   └── event-presentation.tsx                新建：事件名称、图标、颜色的展示映射
│   ├── features/
│   │   ├── today/today-feature.tsx               新建：今日待办列表与跳转预选
│   │   ├── record/record-feature.tsx             新建：事件动作流、默认值和保存反馈
│   │   ├── pets/pets-feature.tsx                 新建：宠物列表与详情 Popup/Drawer
│   │   ├── timeline/timeline-feature.tsx         新建：宠物筛选和倒序事件流
│   │   └── dashboard/dashboard-feature.tsx       新建：近 30 天概览展示
│   ├── pages/
│   │   ├── today-page.tsx                        新建：挂载 TodayFeature
│   │   ├── record-page.tsx                       新建：读取 URL 预选并挂载 RecordFeature
│   │   ├── pets-page.tsx                         新建：挂载 PetsFeature
│   │   ├── timeline-page.tsx                     新建：挂载 TimelineFeature
│   │   └── dashboard-page.tsx                    新建：挂载 DashboardFeature
│   ├── styles/
│   │   └── app.css                               新建：应用布局、断点和安全区
│   └── test/
│       └── setup.ts                              新建：Testing Library 与 DOM Matchers 初始化
└── src/**/*.test.tsx                             新建：页面/feature 的关键交互测试
```

旧的 `src/App.tsx`、`src/App.css`、`src/mockData.tsx`、`src/types.ts`、`src/components/` 与旧 PascalCase `src/pages/` 均由上述新结构替代并删除；不得保留重复的数据模型、布局或页面实现。

## Task 1: 建立可测试的前端基础与目录边界

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/styles/app.css`
- Delete: `frontend/src/App.tsx`
- Delete: `frontend/src/App.css`
- Delete: `frontend/src/mockData.tsx`
- Delete: `frontend/src/types.ts`
- Delete: `frontend/src/components/AppChrome.tsx`
- Delete: `frontend/src/components/BottomNav.tsx`
- Delete: `frontend/src/components/PetCard.tsx`
- Delete: `frontend/src/components/TaskCard.tsx`
- Delete: `frontend/src/pages/DashboardPage.tsx`
- Delete: `frontend/src/pages/PetsPage.tsx`
- Delete: `frontend/src/pages/RecordPage.tsx`
- Delete: `frontend/src/pages/TimelinePage.tsx`
- Delete: `frontend/src/pages/TodayPage.tsx`

**Consumes:** 当前 React 18 + Vite + antd 工程。

**Produces:** 具备 `dev`、`build`、`typecheck`、`test` 脚本的新工程基础；可供后续任务直接创建 `app`、`entities`、`mocks`、`features`、`pages`、`shared`、`styles` 目录。

- [ ] **Step 1: 写出工具链约束测试清单**

在任务笔记中确认以下命令和预期结果，后续实现以此为完成门槛：

```text
npm run typecheck  -> tsc --noEmit 成功退出
npm run test       -> vitest run 成功退出
npm run build      -> vite build 成功退出
```

- [ ] **Step 2: 更新依赖与脚本**

将 `package.json` 合并为以下关键字段（保留已有版本号和 lockfile 管理方式）：

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc -b && vite build",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": {
    "@ant-design/icons": "^6.3.1",
    "@vitejs/plugin-react": "^4.3.0",
    "antd": "^6.4.5",
    "antd-mobile": "^5.42.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.0.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "jsdom": "^25.0.1",
    "vitest": "^2.1.8"
  }
}
```

安装后只保留一个前端 lockfile：以仓库当前实际包管理器为准；若当前工作流使用 npm，删除 `pnpm-lock.yaml`，保留 `package-lock.json`。

- [ ] **Step 3: 配置 Vitest 并加入测试初始化**

扩展 `vite.config.ts`：

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173 },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
```

创建 `src/test/setup.ts`：

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 4: 重建入口与全局样式入口**

将 `src/main.tsx` 收敛成：

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "antd/dist/reset.css";
import "antd-mobile/es/global";
import { App } from "./app/App";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

创建 `src/styles/app.css`，仅包含以下应用框架规则：

```css
:root { color: #24302a; background: #f5f7f3; font-synthesis: none; }
* { box-sizing: border-box; }
html, body, #root { min-width: 320px; min-height: 100%; margin: 0; }
body { min-height: 100vh; }
.app-mobile-content { padding: 12px 12px calc(72px + env(safe-area-inset-bottom)); }
.app-desktop-content { width: min(1120px, 100%); margin: 0 auto; padding: 24px; }
@media (min-width: 768px) and (max-width: 991px) { .app-mobile-content { max-width: 760px; margin: 0 auto; padding: 20px 20px calc(72px + env(safe-area-inset-bottom)); } }
@media (min-width: 992px) { .app-mobile-content { padding: 0; } }
```

- [ ] **Step 5: 删除旧静态原型结构**

删除文件结构表中列出的旧 `App`、旧 Mock、旧类型、旧 components 和旧 pages。确认 `src` 内不再存在旧 `mockData`、`types`、`components` 或同一页面的 PascalCase 版本。

- [ ] **Step 6: 验证工具链基础**

运行：`npm run typecheck && npm run test && npm run build`

预期：在 Task 2 创建 `app/App.tsx` 之前，类型检查会因入口缺失失败。这是预期的红灯；不要通过保留旧 `App.tsx` 来绕过。安装依赖及配置无语法错误即可进入下一任务。

## Task 2: 定义领域模型、初始数据与可订阅内存仓库

**Files:**
- Create: `frontend/src/entities/pet/model.ts`
- Create: `frontend/src/entities/event/model.ts`
- Create: `frontend/src/entities/care-task/model.ts`
- Create: `frontend/src/entities/dashboard/model.ts`
- Create: `frontend/src/shared/date.ts`
- Create: `frontend/src/mocks/initial-data.ts`
- Create: `frontend/src/mocks/derive.ts`
- Create: `frontend/src/mocks/repository.ts`
- Create: `frontend/src/mocks/repository.test.ts`

**Consumes:** Task 1 的 TypeScript 与 Vitest 配置。

**Produces:** `HerpRepository`、`createHerpRepository()`、`deriveCareTasks()`、`deriveDashboardSummary()`，为所有页面提供唯一状态源。

- [ ] **Step 1: 写失败测试，固定仓库可观察行为**

在 `src/mocks/repository.test.ts` 写入：

```ts
import { describe, expect, it } from "vitest";
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
```

在首行补充 `import { vi } from "vitest";`。 

- [ ] **Step 2: 运行测试确认红灯**

运行：`npm run test -- src/mocks/repository.test.ts`

预期：FAIL，提示无法解析 `./repository`。

- [ ] **Step 3: 定义稳定的领域接口**

创建 `entities` 下模型，接口名称和字段必须如下：

```ts
// entities/pet/model.ts
export type PetStatus = "normal" | "observe" | "brumation";
export interface CareRule { feedWindowDays?: readonly [number, number]; weighEveryDays?: number; }
export interface Pet { id: string; name: string; species: string; morph: string; status: PetStatus; avatarColor: string; careRule: CareRule; }
export interface PetSummary extends Pet { latestWeightGram?: number; nextCareText: string; }

// entities/event/model.ts
export type EventType = "feed" | "weight" | "poop" | "shed" | "photo";
export type FeedOutcome = "ate" | "refused";
export type Condition = "normal" | "abnormal";
export interface Event { id: string; petId: string; type: EventType; occurredAt: Date; outcome?: FeedOutcome; condition?: Condition; food?: string; amountGram?: number; weightGram?: number; note: string; }
export interface EventDraft { petId: string; type: EventType; occurredAt: Date; outcome?: FeedOutcome; condition?: Condition; food?: string; amountGram?: number; weightGram?: number; note: string; }

// entities/care-task/model.ts
import type { EventType } from "../event/model";
import type { PetStatus } from "../pet/model";
export type CareTaskTone = "success" | "warning" | "danger";
export interface CareTask { id: string; petId: string; petName: string; petStatus: PetStatus; type: Extract<EventType, "feed" | "weight">; title: string; detail: string; tone: CareTaskTone; }

// entities/dashboard/model.ts
export interface DashboardSummary { recordCount: number; feedCount: number; weightChangeGram: number; abnormalEventCount: number; healthText: string; }
```

- [ ] **Step 4: 实现相对日期初始数据与纯派生函数**

`initial-data.ts` 必须用 `daysAgo(days: number)` 构造日期，不能写固定年份日期；至少提供三只宠物：小黑（玉米蛇，正常，喂食规则 `[5, 7]`）、阿黄（豹纹守宫，观察中，规则 `[3, 4]`）、小绿（睫角守宫，冬化，规则 `[6, 8]`）。事件覆盖 `feed`、`weight`、`poop`、`shed`、`photo`，且让小黑当前处于喂食警告/超期、阿黄有体重待办、小绿不出现喂食待办。

`derive.ts` 必须导出：

```ts
export function deriveCareTasks(pets: readonly Pet[], events: readonly Event[], now: Date): CareTask[]
export function derivePetSummaries(pets: readonly Pet[], events: readonly Event[], now: Date): PetSummary[]
export function deriveDashboardSummary(events: readonly Event[], now: Date): DashboardSummary
export function getLatestEvent(events: readonly Event[], petId: string, type: EventType): Event | undefined
```

实现规则：`feedWindowDays` 的最小天数前为 `success`、区间内为 `warning`、超过最大天数为 `danger`；`brumation` 跳过所有喂食待办；`weighEveryDays` 达到周期后生成体重待办；事件按 `occurredAt` 倒序；近 30 天体重变化为窗口内最早和最新体重事件的差；拒食和 `condition === "abnormal"` 为异常。

- [ ] **Step 5: 实现仓库与订阅协议**

`repository.ts` 必须导出下列接口与工厂：

```ts
export interface HerpRepository {
  getPets(): readonly PetSummary[];
  getEvents(petId?: string): readonly Event[];
  getCareTasks(): readonly CareTask[];
  getDashboardSummary(): DashboardSummary;
  getLatestEvent(petId: string, type: EventType): Event | undefined;
  saveEvent(draft: EventDraft): Event;
  subscribe(listener: () => void): () => void;
}
export function createHerpRepository(now?: () => Date): HerpRepository;
```

`createHerpRepository` 每次调用深复制 `initialPets` 和 `initialEvents`；`saveEvent` 用 `crypto.randomUUID()` 创建 ID，将新 Event 插入数组并按时间倒序，再依次通知所有 listener；所有 getter 在读取时以 `now()` 重新计算派生结果。

- [ ] **Step 6: 运行仓库测试确认绿灯**

运行：`npm run test -- src/mocks/repository.test.ts`

预期：3 个测试 PASS。

## Task 3: 连接仓库到 React，并建立双端路由壳层

**Files:**
- Create: `frontend/src/app/store-context.tsx`
- Create: `frontend/src/app/navigation.tsx`
- Create: `frontend/src/app/app-shell.tsx`
- Create: `frontend/src/app/App.tsx`
- Create: `frontend/src/app/App.test.tsx`

**Consumes:** `HerpRepository` 与 `createHerpRepository()`（Task 2）。

**Produces:** `AppStoreProvider`、`useHerpStore()`、`useHerpSnapshot()`，以及通过 React Router 可访问的 `/today`、`/record`、`/pets`、`/timeline`、`/dashboard` 路由。

- [ ] **Step 1: 写失败测试，验证双端导航语义**

创建 `app/App.test.tsx`：

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { App } from "./App";

describe("App", () => {
  it("将根路径重定向到今日页", async () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "今天" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试确认红灯**

运行：`npm run test -- src/app/App.test.tsx`

预期：FAIL，提示无法解析 `./App`。

- [ ] **Step 3: 实现 Store Context**

`store-context.tsx` 使用 React `createContext` 和 `useSyncExternalStore`，导出：

```tsx
export function AppStoreProvider({ children }: { children: ReactNode }): JSX.Element
export function useHerpStore(): HerpRepository
export function useHerpSnapshot(): {
  pets: readonly PetSummary[];
  events: readonly Event[];
  careTasks: readonly CareTask[];
  dashboard: DashboardSummary;
}
```

Provider 只通过 `useRef` 创建一次 `createHerpRepository()`；`useHerpSnapshot` 用 `useSyncExternalStore(store.subscribe, getSnapshot, getSnapshot)` 订阅，并让 `getSnapshot` 返回稳定的版本号和派生数据，避免无限重渲染。

- [ ] **Step 4: 实现导航定义与应用壳层**

`navigation.tsx` 导出一个 `NavigationItem[]`，字段为 `key`、`path`、`label`、`icon`、`title`，5 项顺序固定为今日、记录、宠物、时间线、概览，并使用 `@ant-design/icons`。

`app-shell.tsx` 必须导出 `AppShell({ children }: { children: ReactNode })`。壳层：

```tsx
const isDesktop = useMediaQuery("(min-width: 992px)");
return isDesktop ? (
  <Layout className="app-desktop-layout">
    <Sider width={232}><Menu mode="inline" items={menuItems} selectedKeys={[activeKey]} onClick={navigateToKey} /></Sider>
    <Layout><Header>{title}</Header><Content><main className="app-desktop-content">{children}</main></Content></Layout>
  </Layout>
) : (
  <div className="app-mobile-layout">
    <NavBar back={null}>{title}</NavBar>
    <main className="app-mobile-content">{children}</main>
    <TabBar safeArea value={activeKey} onChange={navigateToKey}>{tabItems}</TabBar>
  </div>
);
```

`useMediaQuery` 是应用级小 Hook，只负责 `matchMedia` 状态，不产生视觉组件；服务端初始值为 `false`。

- [ ] **Step 5: 实现路由应用**

`App.tsx` 使用 `BrowserRouter`（若已有 Router 上下文则不再包裹）、`AppStoreProvider`、`AppShell` 与 `Routes`。将 `/` 重定向至 `/today`，页面路由分别为 `/today`、`/record`、`/pets`、`/timeline`、`/dashboard`。本任务可暂时用每页 `<div />` 占位，下一任务替换为实际页面；但 `today-page.tsx` 必须先提供 `<h1>今天</h1>` 使测试通过。

- [ ] **Step 6: 运行壳层测试**

运行：`npm run test -- src/app/App.test.tsx`

预期：PASS，根路径最终显示“今天”。

## Task 4: 实现今日待办与跨页预选记录流程

**Files:**
- Create: `frontend/src/features/today/today-feature.tsx`
- Create: `frontend/src/pages/today-page.tsx`
- Create: `frontend/src/features/today/today-feature.test.tsx`
- Modify: `frontend/src/app/App.tsx`

**Consumes:** `useHerpSnapshot()`、`CareTask`、导航路径 `/record`（Task 2–3）。

**Produces:** `TodayFeature`。点击任何待办进入 `/record?petId=<id>&type=<eventType>`；无待办时显示 antd-mobile `Empty`。

- [ ] **Step 1: 写失败测试**

```tsx
it("点击待办时带着宠物和事件类型跳转到记录页", async () => {
  const user = userEvent.setup();
  render(<TodayFeature />, { wrapper: TestAppStoreProvider });
  await user.click(screen.getByRole("button", { name: /建议喂食/ }));
  expect(mockNavigate).toHaveBeenCalledWith(expect.stringMatching(/^\/record\?petId=.+&type=feed$/));
});
```

测试 helper 必须向 feature 提供真实 `AppStoreProvider` 与受控 `MemoryRouter`；mock `useNavigate`，不 mock Mock 仓库。

- [ ] **Step 2: 运行测试确认红灯**

运行：`npm run test -- src/features/today/today-feature.test.tsx`

预期：FAIL，提示 `TodayFeature` 未导出。

- [ ] **Step 3: 实现 TodayFeature**

从 `useHerpSnapshot().careTasks` 读取数据。移动布局使用 antd-mobile `List`、`Card`、`Tag`、`Button` 或 `Grid`；桌面布局可在同一 feature 内使用 antd `List`/`Card`，但不复制业务循环和事件处理。每项展示 `petName`、`title`、`detail` 和用 `tone` 映射的提醒文案。把点击处理集中为：

```ts
function openRecord(task: CareTask): void {
  navigate(`/record?petId=${task.petId}&type=${task.type}`);
}
```

今日为空时渲染 `Empty description="今天没有待办事项"`，不创建自定义空状态组件。

- [ ] **Step 4: 挂载页面路由**

`pages/today-page.tsx` 仅导出：

```tsx
export function TodayPage(): JSX.Element {
  return <TodayFeature />;
}
```

在 `App.tsx` 使用 `TodayPage` 替换 Task 3 的临时标题节点。

- [ ] **Step 5: 运行今日交互测试**

运行：`npm run test -- src/features/today/today-feature.test.tsx`

预期：PASS，点击待办生成正确的 `/record` 查询参数。

## Task 5: 实现快速记录动作流与全局数据联动

**Files:**
- Create: `frontend/src/features/record/record-feature.tsx`
- Create: `frontend/src/pages/record-page.tsx`
- Create: `frontend/src/features/record/record-feature.test.tsx`
- Modify: `frontend/src/app/App.tsx`

**Consumes:** `useHerpStore()`、`useHerpSnapshot()`、`EventDraft`、`EventType`、`getLatestEvent()`、记录预选 URL（Task 2–4）。

**Produces:** `RecordFeature`；可保存 5 类事件，保存后仓库更新且 `Toast.show({ content: "已保存" })`。

- [ ] **Step 1: 写失败测试，验证记录联动**

```tsx
it("保存喂食后在时间线数据中新增事件并移除今日喂食待办", async () => {
  const user = userEvent.setup();
  const repository = createHerpRepository();
  render(<RecordFeature initialPetId="pet-1" initialType="feed" />, { wrapper: ({ children }) => <TestAppStoreProvider store={repository}>{children}</TestAppStoreProvider> });

  await user.click(screen.getByRole("button", { name: "保存记录" }));

  expect(repository.getEvents()[0]).toMatchObject({ petId: "pet-1", type: "feed", outcome: "ate" });
  expect(repository.getCareTasks().some((task) => task.petId === "pet-1" && task.type === "feed")).toBe(false);
});
```

- [ ] **Step 2: 运行测试确认红灯**

运行：`npm run test -- src/features/record/record-feature.test.tsx`

预期：FAIL，提示 `RecordFeature` 未导出。

- [ ] **Step 3: 实现预选解析和共用表单基础**

`RecordPage` 用 `useSearchParams()` 读取 `petId` 和 `type`，验证它们是否分别存在于当前宠物与 `EventType` 集合中；无效值回退为第一只宠物和 `feed`。页面仅将解析后的值传给：

```tsx
<RecordFeature initialPetId={petId} initialType={type} />
```

Feature 使用 antd-mobile `Form`、`Selector`、`Input`、`InputNumber`、`TextArea` 和 `Button`。宠物与事件类型都用组件库的选择控件；不可使用手写按钮组。

- [ ] **Step 4: 实现五种最小动作流和默认值**

选择宠物或类型后，读取 `store.getLatestEvent(petId, type)`：

```ts
const defaults = {
  feed: { outcome: latest?.outcome ?? "ate", food: latest?.food ?? "冻鼠", amountGram: latest?.amountGram ?? 18 },
  weight: { weightGram: latest?.weightGram },
  poop: { condition: latest?.condition ?? "normal", note: "" },
  shed: { condition: latest?.condition ?? "normal", note: "" },
  photo: { note: "" },
};
```

字段要求：

| 类型 | 必填字段 | 可选字段 |
|---|---|---|
| `feed` | `outcome`、`food`、`amountGram` | `note` |
| `weight` | `weightGram` | `note` |
| `poop` | `condition` | `note`，仅异常时显示 |
| `shed` | `condition` | `note`，仅异常时显示 |
| `photo` | 无 | `note` |

`amountGram` 与 `weightGram` 必须大于 0。使用 Form `rules` 提示必填/数值错误，禁止手写校验 UI。

- [ ] **Step 5: 实现统一保存入口**

按钮提交时仅构造 `EventDraft` 并调用 `store.saveEvent(draft)`：

```ts
const event = store.saveEvent({
  petId,
  type,
  occurredAt: new Date(),
  outcome: values.outcome,
  condition: values.condition,
  food: values.food?.trim(),
  amountGram: values.amountGram,
  weightGram: values.weightGram,
  note: values.note?.trim() ?? "",
});
Toast.show({ content: "已保存" });
form.clear();
setSelectedType(event.type);
```

保存成功后保留在当前页，使用组件库 `Grid` 或 `Button` 提供喂食、体重、排泄、蜕皮、照片的继续记录快捷入口。点击快捷入口只改变 `selectedType` 并载入该类型默认值。

- [ ] **Step 6: 运行记录联动测试**

运行：`npm run test -- src/features/record/record-feature.test.tsx`

预期：PASS，默认喂食提交后事件位于仓库时间线首位，目标喂食待办消失。

## Task 6: 实现宠物列表、详情和事件时间线

**Files:**
- Create: `frontend/src/features/pets/pets-feature.tsx`
- Create: `frontend/src/features/timeline/timeline-feature.tsx`
- Create: `frontend/src/pages/pets-page.tsx`
- Create: `frontend/src/pages/timeline-page.tsx`
- Create: `frontend/src/features/timeline/timeline-feature.test.tsx`
- Modify: `frontend/src/app/App.tsx`

**Consumes:** `PetSummary`、`Event`、`useHerpSnapshot()`、`useHerpStore()`、`event-presentation`（Task 2–5）。

**Produces:** 宠物列表及 Popup/Drawer 详情；可按全部或单宠物筛选且倒序刷新的时间线。

- [ ] **Step 1: 写失败测试，验证时间线筛选和新增事件显示**

```tsx
it("按宠物筛选时间线，并将新保存事件放在最顶部", async () => {
  const user = userEvent.setup();
  const repository = createHerpRepository();
  render(<TimelineFeature />, { wrapper: ({ children }) => <TestAppStoreProvider store={repository}>{children}</TestAppStoreProvider> });

  await user.click(screen.getByRole("button", { name: "小黑" }));
  expect(screen.queryByText(/阿黄/)).not.toBeInTheDocument();

  repository.saveEvent({ petId: "pet-1", type: "photo", occurredAt: new Date(), note: "最新照片" });
  expect(await screen.findByText("最新照片")).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认红灯**

运行：`npm run test -- src/features/timeline/timeline-feature.test.tsx`

预期：FAIL，提示 `TimelineFeature` 未导出。

- [ ] **Step 3: 实现展示映射与时间线**

创建 `shared/event-presentation.tsx` 并导出：

```tsx
export function eventLabel(type: EventType): string
export function eventIcon(type: EventType): ReactNode
export function eventDescription(event: Event): string
```

使用 `@ant-design/icons`，映射必须覆盖全部 5 种事件；`eventDescription` 对喂食显示“吃了/拒食 · 食物 · 重量”，对体重显示“体重 462g”，对排泄/蜕皮显示正常或异常，对照片显示备注或“新增照片记录”。

`TimelineFeature` 使用 `Selector` 或 `ActionSheet` 提供“全部”和每只宠物筛选项，从 `snapshot.events` 读取并按 `occurredAt` 倒序渲染 antd-mobile `List`。每项展示图标、宠物名、格式化时间、主要描述和异常标签；没有结果时显示 `Empty description="没有匹配的记录"`。

- [ ] **Step 4: 实现宠物列表与详情**

`PetsFeature` 从 `snapshot.pets` 读取数据并用 antd-mobile `List`/`Card` 展示名称、物种、状态、最近体重和 `nextCareText`。点击一行仅设置选择宠物并打开 `Popup`；Popup 内使用 `List` 显示档案摘要和该宠物最近 3 个事件。桌面断点下可用 antd `Drawer`，但详情数据与选择状态只维护一套。

- [ ] **Step 5: 挂载两个页面和路由**

页面文件仅封装对应 feature：

```tsx
export function PetsPage(): JSX.Element { return <PetsFeature />; }
export function TimelinePage(): JSX.Element { return <TimelineFeature />; }
```

更新 `App.tsx`，将 `/pets` 与 `/timeline` 路由连接到两个页面。

- [ ] **Step 6: 运行时间线测试**

运行：`npm run test -- src/features/timeline/timeline-feature.test.tsx`

预期：PASS，筛选只显示选择宠物，新事件即时出现。

## Task 7: 实现近 30 天概览和端到端业务验证

**Files:**
- Create: `frontend/src/features/dashboard/dashboard-feature.tsx`
- Create: `frontend/src/pages/dashboard-page.tsx`
- Create: `frontend/src/features/dashboard/dashboard-feature.test.tsx`
- Create: `frontend/src/app/app-flow.test.tsx`
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/styles/app.css`

**Consumes:** `DashboardSummary`、`useHerpSnapshot()`、`deriveDashboardSummary()` 和所有页面路由（Task 2–6）。

**Produces:** 概览页面以及覆盖保存事件到多页面刷新、双端布局无溢出的自动/浏览器验证入口。

- [ ] **Step 1: 写失败测试，验证概览由事件推导**

```tsx
it("显示仓库推导出的近 30 天统计", () => {
  render(<DashboardFeature />, { wrapper: TestAppStoreProvider });
  expect(screen.getByText("近 30 天")).toBeInTheDocument();
  expect(screen.getByText(/记录/)).toBeInTheDocument();
  expect(screen.getByText(/喂食/)).toBeInTheDocument();
  expect(screen.getByText(/异常/)).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认红灯**

运行：`npm run test -- src/features/dashboard/dashboard-feature.test.tsx`

预期：FAIL，提示 `DashboardFeature` 未导出。

- [ ] **Step 3: 实现 DashboardFeature 并挂载路由**

从 `useHerpSnapshot().dashboard` 读取数据；移动端使用 antd-mobile `Card`、`Grid`、`Tag`，桌面端使用 antd `Card`、`Row`、`Col`、`Statistic`。显示标题“近 30 天”、`healthText`，以及以下四项唯一来源为派生摘要的数值：

```ts
[
  ["记录", dashboard.recordCount],
  ["喂食", dashboard.feedCount],
  ["体重变化", `${dashboard.weightChangeGram >= 0 ? "+" : ""}${dashboard.weightChangeGram}g`],
  ["异常", dashboard.abnormalEventCount],
]
```

创建 `DashboardPage` 并在 `/dashboard` 挂载；所有页面路由不得再用占位节点。

- [ ] **Step 4: 写并运行端到端组件流测试**

`app-flow.test.tsx` 使用 `MemoryRouter`、真实 `AppStoreProvider` 和 `userEvent`：从 `/today` 点击小黑喂食待办，断言进入预选记录页；点击“保存记录”；导航到时间线并断言新增事件；导航到概览并断言记录数可见。测试必须断言状态变化，不仅断言页面文本。

运行：`npm run test -- src/app/app-flow.test.tsx`

预期：PASS。

- [ ] **Step 5: 完善仅限框架的响应式 CSS**

在 `styles/app.css` 增加且仅增加布局规则：移动 `TabBar` 固定于底部、桌面 `Sider` 高度 100vh、桌面隐藏移动 `TabBar`、移动隐藏桌面布局；页面内容使用 `overflow-x: hidden` 防止横向溢出；Desktop Content 使用 `min-width: 0`。禁止新增组件库组件样式覆盖。

- [ ] **Step 6: 完整自动验证**

运行：`npm run typecheck && npm run test && npm run build`

预期：所有命令成功退出；Vitest 全绿；`dist/` 生成成功。

- [ ] **Step 7: 浏览器响应式验收**

运行开发服务器：`npm run dev`。在浏览器依次设置宽度 320px、390px、768px、1024px、1440px，并逐项确认：

```text
[ ] 320px：底部 TabBar 可点击，最后一项内容没有被遮挡，无横向滚动
[ ] 390px：快速记录表单的所有输入和保存按钮可见、可操作
[ ] 768px：保持移动导航，内容宽度和间距扩大但没有侧栏挤压
[ ] 1024px：显示桌面侧栏且隐藏底部 TabBar，内容区域无溢出
[ ] 1440px：内容最大宽度保持 1120px，表单和统计栅格不塌陷
[ ] 喂食：保存后对应今日待办消失，时间线顶部新增事件，宠物下一项与概览更新
[ ] 体重、排泄、蜕皮、照片：各保存一次，均出现在时间线且概览数值更新
[ ] 冬化宠物：今日页没有喂食待办
[ ] 时间线：选择无事件宠物/条件时显示组件库 Empty
[ ] 刷新：所有数据恢复初始 Mock 状态
```

如发现横向滚动、导航遮挡、字段不可操作或联动失败，先新增对应失败测试，再修正最小实现并重复完整自动验证。

## 计划自检

- **规格覆盖：** Task 1 覆盖组件库、工具链与旧结构删除；Task 2 覆盖领域、相对日期、规则、单一 Mock 数据源；Task 3 覆盖路由及移动/桌面壳层；Task 4 至 7 覆盖五个页面、保存联动、校验、空态、提示和响应式验收。
- **范围控制：** 未包含 API、持久化、登录、图片上传、Care Plan 编辑、日历和复杂图表。
- **类型一致性：** `EventDraft` 是唯一写入参数；`HerpRepository.saveEvent()` 是唯一写入入口；`CareTask` 只包含 feed/weight；所有 feature 从 `useHerpStore()`/`useHerpSnapshot()` 获取数据。
- **占位扫描：** 本计划不含 TBD、TODO、"稍后实现" 或无具体接口的实现步骤。
