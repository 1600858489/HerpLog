import { BellOutlined } from "@ant-design/icons";
import { Avatar, Badge, Button, Flex, Layout, Menu, Space, Typography } from "antd";
import type { MenuProps } from "antd";
import type { ReactNode } from "react";
import { BottomNav } from "./BottomNav";
import type { NavItem, PageKey } from "../types";

const { Header, Sider, Content } = Layout;
const { Text, Title } = Typography;

interface AppChromeProps {
  activeKey: PageKey;
  children: ReactNode;
  navItems: NavItem[];
  notificationCount: number;
  pageTitle: string;
  pageSubtitle: string;
  onNavigate: (key: PageKey) => void;
}

export function AppChrome({
  activeKey,
  children,
  navItems,
  notificationCount,
  pageTitle,
  pageSubtitle,
  onNavigate,
}: AppChromeProps) {
  const menuItems: MenuProps["items"] = navItems.map((item: NavItem) => ({
    key: item.key,
    icon: item.icon,
    label: item.label,
  }));

  return (
    <Layout className="app-layout">
      <Sider className="app-sider" width={232}>
        <div className="brand">
          <Avatar size={42} style={{ backgroundColor: "#3f7d58" }}>
            鳞
          </Avatar>
          <div>
            <Text strong>鳞记</Text>
            <Text type="secondary" className="brand-subtitle">
              HerpLog
            </Text>
          </div>
        </div>
        <Menu
          className="side-menu"
          items={menuItems}
          mode="inline"
          selectedKeys={[activeKey]}
          onClick={({ key }) => onNavigate(key as PageKey)}
        />
      </Sider>

      <Layout className="main-layout">
        <Header className="app-header">
          <Flex align="center" justify="space-between" gap={16}>
            <div>
              <Title level={3} className="page-title">
                {pageTitle}
              </Title>
              <Text type="secondary">{pageSubtitle}</Text>
            </div>
            <Space>
              <Badge count={notificationCount} size="small">
                <Button icon={<BellOutlined />} />
              </Badge>
            </Space>
          </Flex>
        </Header>

        <Content className="app-content">{children}</Content>
      </Layout>

      <BottomNav activeKey={activeKey} items={navItems} onChange={onNavigate} />
    </Layout>
  );
}
