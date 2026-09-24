import { Card, Col, Divider, Row, Statistic, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { RouteOverview, TeamResultRecord } from "../types";
import { ResultsTable } from "./ResultsTable";

interface RoutePanelProps {
  overview: RouteOverview;
  onRevoke: (record: TeamResultRecord) => void;
  revokingId: number | null;
}

const revokedColumns: ColumnsType<TeamResultRecord> = [
  { title: "队名", dataIndex: "teamName", key: "teamName", width: 140 },
  {
    title: "原状态",
    dataIndex: "previousStatusLabel",
    key: "previousStatusLabel",
    width: 100,
    render: (label: string) => <Tag>{label}</Tag>,
  },
  { title: "原用时", dataIndex: "duration", key: "duration", width: 110 },
  {
    title: "撤销原因",
    dataIndex: "revokeReason",
    key: "revokeReason",
    render: (reason: string) => reason || <Typography.Text type="secondary">未填写</Typography.Text>,
  },
  {
    title: "撤销时间",
    dataIndex: "revokedAt",
    key: "revokedAt",
    width: 190,
    render: (value: string | null) => (value ? new Date(value).toLocaleString() : "—"),
  },
];

export function RoutePanel({ overview, onRevoke, revokingId }: RoutePanelProps) {
  const { route, records, pendingTeams, revokedRecords, summary } = overview;

  return (
    <Card
      className="settle-card route-panel"
      title={
        <div className="route-panel-title">
          <span>{route.name}</span>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            {route.description}
          </Typography.Text>
        </div>
      }
      extra={
        <div className="tag-row">
          {route.checkpointSequence.map((code, index) => (
            <Tag color="blue" key={code}>
              {index + 1}. {code}
            </Tag>
          ))}
        </div>
      }
    >
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Statistic title="完成队伍" value={summary.completedCount} valueStyle={{ color: "#3f8600" }} />
        </Col>
        <Col xs={12} md={6}>
          <Statistic title="未完成队伍" value={summary.incompleteCount} valueStyle={{ color: "#d46b08" }} />
        </Col>
        <Col xs={12} md={6}>
          <Statistic title="待结算队伍" value={summary.pendingCount} valueStyle={{ color: "#8c8c8c" }} />
        </Col>
        <Col xs={12} md={6}>
          <Statistic title="已撤销记录" value={summary.revokedCount} valueStyle={{ color: "#595959" }} />
        </Col>
      </Row>

      {pendingTeams.length > 0 && (
        <div className="pending-block">
          <Typography.Text strong>待结算队伍：</Typography.Text>
          {pendingTeams.map((name) => (
            <Tag color="gold" key={name}>
              {name}
            </Tag>
          ))}
          <Typography.Text type="secondary">
            （成绩撤销后回到待结算，可重新提交）
          </Typography.Text>
        </div>
      )}

      <ResultsTable records={records} onRevoke={onRevoke} revokingId={revokingId} />

      {revokedRecords.length > 0 && (
        <>
          <Divider orientation="left">撤销历史（不参与排名，仅留档）</Divider>
          <Table
            columns={revokedColumns}
            dataSource={revokedRecords}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </>
      )}
    </Card>
  );
}
