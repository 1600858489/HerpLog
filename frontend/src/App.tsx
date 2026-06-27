import { useMemo, useState } from "react";
import { ConfigProvider, theme } from "antd";
import { AppChrome } from "./components/AppChrome";
import { careTasks, metrics, navItems, pets, timelineEvents } from "./mockData";
import { DashboardPage } from "./pages/DashboardPage";
import { PetsPage } from "./pages/PetsPage";
import { RecordPage } from "./pages/RecordPage";
import { TimelinePage } from "./pages/TimelinePage";
import { TodayPage } from "./pages/TodayPage";
import type { PageKey } from "./types";
import "./App.css";

const pageMeta: Record<PageKey, { title: string; subtitle: string }> = {
  today: { title: "今天", subtitle: "只保留当下最需要处理的事。" },
  record: { title: "快速记录", subtitle: "一个页面内完成主要操作。" },
  pets: { title: "宠物", subtitle: "查看每只爬宠的当前状态。" },
  timeline: { title: "时间线", subtitle: "按时间回看发生过的事。" },
  dashboard: { title: "概览", subtitle: "用少量指标判断整体趋势。" },
};

function App() {
  const [activePage, setActivePage] = useState<PageKey>("today");
  const meta = pageMeta[activePage];

  const pageContent = useMemo(() => {
    switch (activePage) {
      case "record":
        return <RecordPage />;
      case "pets":
        return <PetsPage pets={pets} />;
      case "timeline":
        return <TimelinePage events={timelineEvents} />;
      case "dashboard":
        return <DashboardPage metrics={metrics} />;
      case "today":
      default:
        return (
          <TodayPage metrics={metrics} tasks={careTasks} onRecord={() => setActivePage("record")} />
        );
    }
  }, [activePage]);

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#3f7d58",
          borderRadius: 8,
          colorBgLayout: "#f5f7f3",
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        },
      }}
    >
      <AppChrome
        activeKey={activePage}
        navItems={navItems}
        notificationCount={careTasks.length}
        pageSubtitle={meta.subtitle}
        pageTitle={meta.title}
        onNavigate={setActivePage}
      >
        {pageContent}
      </AppChrome>
    </ConfigProvider>
  );
}

export default App;
