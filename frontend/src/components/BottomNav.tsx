import { Button, Flex } from "antd";
import type { NavItem, PageKey } from "../types";

interface BottomNavProps {
  activeKey: PageKey;
  items: NavItem[];
  onChange: (key: PageKey) => void;
}

export function BottomNav({ activeKey, items, onChange }: BottomNavProps) {
  return (
    <nav className="bottom-nav" aria-label="主导航">
      <Flex justify="space-around" align="center" gap={4}>
        {items.map((item: NavItem) => (
          <Button
            className={item.key === activeKey ? "bottom-nav-item active" : "bottom-nav-item"}
            icon={item.icon}
            key={item.key}
            type="text"
            onClick={() => onChange(item.key)}
          >
            {item.label}
          </Button>
        ))}
      </Flex>
    </nav>
  );
}
