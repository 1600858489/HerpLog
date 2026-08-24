import { Layout, Menu, Typography } from "antd";
import { NavBar, TabBar } from "antd-mobile";
import { type ReactNode, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { navigationForPath, navigationItems, type NavigationKey } from "./navigation";

const { Header, Sider, Content } = Layout;

function useDesktopLayout(): boolean {
  const query = "(min-width: 992px)";
  const [isDesktop, setIsDesktop] = useState(() => window.matchMedia(query).matches);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const update = () => setIsDesktop(mediaQuery.matches);
    mediaQuery.addEventListener("change", update);
    return () => mediaQuery.removeEventListener("change", update);
  }, []);

  return isDesktop;
}

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const activeItem = navigationForPath(location.pathname);
  const isDesktop = useDesktopLayout();
  const navigateToKey = (key: string) => {
    const item = navigationItems.find((candidate) => candidate.key === key as NavigationKey);
    if (item) navigate(item.path);
  };

  if (isDesktop) {
    return (
      <Layout className="app-desktop-layout">
        <Sider width={232} theme="light">
          <div className="app-brand"><Typography.Text strong>鳞记</Typography.Text></div>
          <Menu
            mode="inline"
            selectedKeys={[activeItem.key]}
            items={navigationItems.map(({ key, icon, label }) => ({ key, icon, label }))}
            onClick={({ key }) => navigateToKey(key)}
          />
        </Sider>
        <Layout>
          <Header className="app-desktop-header"><Typography.Title level={3}>{activeItem.title}</Typography.Title></Header>
          <Content><main className="app-desktop-content">{children}</main></Content>
        </Layout>
      </Layout>
    );
  }

  return (
    <div className="app-mobile-layout">
      <NavBar back={null}>{activeItem.title}</NavBar>
      <main className="app-mobile-content">{children}</main>
      <TabBar safeArea activeKey={activeItem.key} onChange={navigateToKey}>
        {navigationItems.map(({ key, icon, label }) => <TabBar.Item key={key} icon={icon} title={label} />)}
      </TabBar>
    </div>
  );
}
