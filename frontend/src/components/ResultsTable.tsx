import { Button, Empty, Popconfirm, Table, Tag, Tooltip, Typography } from "antd";
import { UndoOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { TeamResultRecord } from "../types";
import { REQUEST_MESSAGES } from "../constants/messages";

const { Text } = Typography;

const STATUS_COLOR: Record<string, string> = {
  completed: "green",
  incomplete: "orange",
  revoked: "default",
};

interface ResultsTableProps {
  records: TeamResultRecord[];
  onRevoke: (record: TeamResultRecord) => void;
  revokingId: number | null;
  showRevokeAction?: boolean;
}

export function ResultsTable({
  records,
  onRevoke,
  revokingId,
  showRevokeAction = true,
}: ResultsTableProps) {
  const columns: ColumnsType<TeamResultRecord> = [
    {
      title: "名次",
      dataIndex: "rank",
      key: "rank",
      width: 80,
      render: (rank: number | null) =>
        rank ? <Text strong>第 {rank} 名</Text> : <Text type="secondary">—</Text>,
    },
    { title: "队名", dataIndex: "teamName", key: "teamName", width: 140 },
    {
      title: "总用时",
      dataIndex: "duration",
      key: "duration",
      width: 110,
      render: (duration: string, record) =>
        record.status === "completed" ? (
          <Text strong>{duration}</Text>
        ) : (
          <Text type="secondary">{duration}</Text>
        ),
    },
    {
      title: "提交到点顺序",
      dataIndex: "submittedSequence",
      key: "submittedSequence",
      render: (sequence: string[]) => (
        <span className="sequence-cell">{sequence.join(" → ")}</span>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (_, record) => (
        <Tag color={STATUS_COLOR[record.status]}>{record.statusLabel}</Tag>
      ),
    },
    {
      title: "成绩栏说明",
      dataIndex: "resultNote",
      key: "resultNote",
      render: (note: string, record) => (
        <span className={record.issues.length ? "note-incomplete" : "note-ok"}>
          {note}
          {record.issueLabels.length > 0 && (
            <span className="issue-tags">
              {record.issueLabels.map((label) => (
                <Tag color="red" key={label}>
                  {label}
                </Tag>
              ))}
            </span>
          )}
        </span>
      ),
    },
    ...(showRevokeAction
      ? [
          {
            title: "裁判操作",
            key: "action",
            width: 110,
            render: (_: unknown, record: TeamResultRecord) => (
              <Popconfirm
                title="撤销成绩"
                description={REQUEST_MESSAGES.revokeConfirm}
                okText="确认撤销"
                cancelText="取消"
                okButtonProps={{ danger: true }}
                onConfirm={() => onRevoke(record)}
              >
                <Tooltip title="录错时可撤销一次">
                  <Button
                    danger
                    size="small"
                    icon={<UndoOutlined />}
                    loading={revokingId === record.id}
                  >
                    撤销
                  </Button>
                </Tooltip>
              </Popconfirm>
            ),
          } as ColumnsType<TeamResultRecord>[number],
        ]
      : []),
  ];

  return (
    <Table
      columns={columns}
      dataSource={records}
      rowKey="id"
      pagination={false}
      scroll={{ x: 900 }}
      locale={{ emptyText: <Empty description="暂无成绩记录" /> }}
    />
  );
}
