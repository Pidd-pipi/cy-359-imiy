import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  Input,
  Modal,
  Space,
  Statistic,
  Table,
  Tag,
  Tabs,
  Typography,
} from "antd";
import { UndoOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { ResultsOverview, TeamResult } from "../types";

interface RefereeOverviewProps {
  overview: ResultsOverview;
  revoking: boolean;
  onRevoke: (id: number, reason: string) => void;
}

const STATUS_COLOR: Record<string, string> = {
  pending: "default",
  finished: "success",
  incomplete: "error",
  revoked: "warning",
};

export function RefereeOverview({ overview, revoking, onRevoke }: RefereeOverviewProps) {
  const [revokeTarget, setRevokeTarget] = useState<TeamResult | null>(null);
  const [revokeReason, setRevokeReason] = useState("");

  const confirmRevoke = () => {
    if (revokeTarget?.id != null) {
      onRevoke(revokeTarget.id, revokeReason.trim());
    }
    setRevokeTarget(null);
    setRevokeReason("");
  };

  const teamColumns: ColumnsType<TeamResult> = [
    {
      title: "名次",
      dataIndex: "rank",
      key: "rank",
      width: 80,
      render: (rank: number | null) =>
        rank ? <Tag color="gold">第 {rank} 名</Tag> : <Typography.Text type="secondary">—</Typography.Text>,
    },
    { title: "队名", dataIndex: "teamName", key: "teamName", width: 120 },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (_, record) => <Tag color={STATUS_COLOR[record.status]}>{record.statusLabel}</Tag>,
    },
    {
      title: "总用时",
      dataIndex: "totalTime",
      key: "totalTime",
      width: 110,
      sorter: (a, b) => (a.totalSeconds ?? 0) - (b.totalSeconds ?? 0),
    },
    {
      title: "提交的到点顺序",
      dataIndex: "sequence",
      key: "sequence",
      render: (sequence: string[]) =>
        sequence.length ? sequence.map((code, i) => <Tag key={`${code}-${i}`}>{code}</Tag>) : "—",
    },
    {
      title: "成绩 / 未完成原因",
      dataIndex: "issueReason",
      key: "issueReason",
      render: (reason: string, record) =>
        record.status === "finished" ? (
          <Typography.Text type="success">完赛，成绩有效</Typography.Text>
        ) : record.status === "pending" ? (
          <Typography.Text type="secondary">待结算</Typography.Text>
        ) : (
          <Alert type="warning" style={{ padding: "4px 10px" }} message={reason} />
        ),
    },
    {
      title: "操作",
      key: "action",
      width: 130,
      render: (_, record) =>
        record.revocable && record.id != null ? (
          <Button
            danger
            size="small"
            icon={<UndoOutlined />}
            disabled={revoking}
            onClick={() => {
              setRevokeTarget(record);
              setRevokeReason("");
            }}
          >
            撤销成绩
          </Button>
        ) : (
          <Typography.Text type="secondary">—</Typography.Text>
        ),
    },
  ];

  const revokedColumns: ColumnsType<TeamResult> = [
    { title: "队名", dataIndex: "teamName", key: "teamName", width: 120 },
    { title: "原总用时", dataIndex: "totalTime", key: "totalTime", width: 110 },
    {
      title: "原到点顺序",
      dataIndex: "sequence",
      key: "sequence",
      render: (sequence: string[]) => sequence.map((code, i) => <Tag key={`${code}-${i}`}>{code}</Tag>),
    },
    { title: "撤销/问题说明", dataIndex: "issueReason", key: "issueReason" },
    { title: "撤销时间", dataIndex: "revokedAt", key: "revokedAt", width: 180 },
  ];

  return (
    <div className="referee-overview">
      <Space size={16} wrap className="stat-row">
        {overview.stats.map((stat) => (
          <Card key={stat.key} className="stat-card">
            <Statistic title={stat.label} value={stat.value} />
          </Card>
        ))}
      </Space>

      <Alert
        type="info"
        showIcon
        style={{ margin: "16px 0" }}
        message={`比赛线路：${overview.course.name}｜规定顺序：${overview.course.checkpoints.join(" → ")}`}
      />

      <Tabs
        defaultActiveKey="teams"
        items={[
          {
            key: "teams",
            label: `各队成绩（${overview.teamsResults.length}）`,
            children: (
              <Table<TeamResult>
                rowKey={(record) => String(record.id ?? `pending-${record.teamName}`)}
                columns={teamColumns}
                dataSource={overview.teamsResults}
                pagination={false}
                scroll={{ x: 960 }}
              />
            ),
          },
          {
            key: "ranking",
            label: `实时排名（${overview.ranking.length}）`,
            children: (
              <Table<TeamResult>
                rowKey={(record) => String(record.id)}
                columns={teamColumns}
                dataSource={overview.ranking}
                pagination={false}
                scroll={{ x: 960 }}
              />
            ),
          },
          {
            key: "revoked",
            label: `撤销留痕（${overview.revokedResults.length}）`,
            children: overview.revokedResults.length ? (
              <Table<TeamResult>
                rowKey={(record) => String(record.id)}
                columns={revokedColumns}
                dataSource={overview.revokedResults}
                pagination={false}
              />
            ) : (
              <Typography.Text type="secondary">暂无被撤销的成绩。</Typography.Text>
            ),
          },
        ]}
      />

      <Modal
        title={`撤销「${revokeTarget?.teamName ?? ""}」的成绩`}
        open={revokeTarget !== null}
        onOk={confirmRevoke}
        confirmLoading={revoking}
        okText="确认撤销"
        cancelText="取消"
        okButtonProps={{ danger: true }}
        onCancel={() => setRevokeTarget(null)}
      >
        <Typography.Paragraph type="secondary">
          撤销后该队回到待结算，可重新提交；原成绩保留在「撤销留痕」中，不再参与排名。
        </Typography.Paragraph>
        <Input.TextArea
          rows={3}
          placeholder="可填写撤销原因，如：总用时录错（选填）"
          value={revokeReason}
          onChange={(event) => setRevokeReason(event.target.value)}
        />
      </Modal>
    </div>
  );
}
