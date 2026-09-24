import { Alert, Button, Empty, Space, Spin, Typography } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import type { OverviewResponse, TeamResultRecord } from "../types";
import { RoutePanel } from "./RoutePanel";

interface OverviewBoardProps {
  overview: OverviewResponse | null;
  loading: boolean;
  error: string | null;
  revokingId: number | null;
  onReload: () => void;
  onRevoke: (record: TeamResultRecord) => void;
}

export function OverviewBoard({
  overview,
  loading,
  error,
  revokingId,
  onReload,
  onRevoke,
}: OverviewBoardProps) {
  return (
    <section className="overview-board">
      <div className="overview-head">
        <Typography.Title level={3} style={{ margin: 0 }}>
          裁判总览
        </Typography.Title>
        <Space>
          <Typography.Text type="secondary">
            完成队伍按总用时升序排名；未完成保留记录并标注原因；撤销成绩不参与排名。
          </Typography.Text>
          <Button icon={<ReloadOutlined />} onClick={onReload} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {error && <Alert type="error" showIcon message={error} className="overview-alert" />}

      {loading && !overview && (
        <div className="overview-loading">
          <Spin size="large" />
        </div>
      )}

      {!loading && overview && overview.routes.length === 0 && (
        <Empty description="暂无线路数据" />
      )}

      <div className="route-panel-list">
        {overview?.routes.map((routeOverview) => (
          <RoutePanel
            key={routeOverview.route.id}
            overview={routeOverview}
            onRevoke={onRevoke}
            revokingId={revokingId}
          />
        ))}
      </div>
    </section>
  );
}
