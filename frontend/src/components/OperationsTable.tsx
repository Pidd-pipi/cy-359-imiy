import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { OperationRecord } from "../types";

const columns: ColumnsType<OperationRecord> = [
  { title: "模块", dataIndex: "name", key: "name" },
  { title: "负责人", dataIndex: "owner", key: "owner" },
  { title: "状态", dataIndex: "status", key: "status", render: (value) => <Tag>{value}</Tag> },
  { title: "指标", dataIndex: "metric", key: "metric" },
];

interface OperationsTableProps {
  records: OperationRecord[];
}

export function OperationsTable({ records }: OperationsTableProps) {
  return <Table columns={columns} dataSource={records} pagination={false} rowKey="key" />;
}
