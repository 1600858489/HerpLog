import { Card, Grid, List, Space, Tag } from "antd-mobile";
import { useHerpSnapshot } from "../../app/store-context";

/**
 * 健康概览：回答整体状态、谁需要关注、最近记录是否持续三个问题。
 * 用法：页面直接渲染；所有摘要由事件和宠物档案实时推导。
 */
export function DashboardFeature() {
  const { dashboard } = useHerpSnapshot();
  const values = [
    ["记录", dashboard.recordCount],
    ["喂食", dashboard.feedCount],
    ["体重变化", `${dashboard.weightChangeGram >= 0 ? "+" : ""}${dashboard.weightChangeGram}g`],
    ["异常", dashboard.abnormalEventCount],
  ] as const;
  const attentionCount = dashboard.petInsights.filter((insight) => insight.tone !== "success").length;

  return (
    <Space block direction="vertical" style={{ "--gap": "14px" }}>
      <div className="dashboard-intro">
        <span className="eyebrow">KEEPER'S VIEW</span>
        <h1>照顾全局</h1>
        <p>不用翻遍记录，也能知道每一只现在怎么样。</p>
      </div>
      <Card className="dashboard-health-card" title="最近 30 天" extra={<Tag color={dashboard.abnormalEventCount ? "warning" : "success"}>{dashboard.healthText}</Tag>}>
        <div className="dashboard-health-lead">{attentionCount === 0 ? "今天的爬箱都很安静。" : `${attentionCount} 只宠物值得你看一眼。`}</div>
        <Grid columns={2} gap={12}>
          {values.map(([label, value]) => <Grid.Item key={label}><strong>{value}</strong><div>{label}</div></Grid.Item>)}
        </Grid>
      </Card>
      <Card title="每只宠物的状态">
        <List>
          {dashboard.petInsights.map((insight) => (
            <List.Item key={insight.petId} extra={<Tag color={insight.tone === "danger" ? "danger" : insight.tone === "warning" ? "warning" : "success"}>{insight.headline}</Tag>} description={insight.detail}>
              {insight.petName}
            </List.Item>
          ))}
        </List>
      </Card>
      <Card title="这个页面看什么">
        <p className="dashboard-purpose">这里不是报表，而是照顾视野：看整体趋势、找出需要关注的宠物，再回到今日或时间线处理具体事情。</p>
      </Card>
    </Space>
  );
}
