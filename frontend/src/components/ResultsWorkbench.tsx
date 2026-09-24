import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Result, Space, Spin, Tabs, Typography, message } from "antd";
import { ReloadOutlined, TeamOutlined, AuditOutlined } from "@ant-design/icons";
import { fetchCourse, fetchResultsOverview, revokeResult, submitResult } from "../api/client";
import type { CourseDetail, ResultsOverview, SubmitPayload } from "../types";
import { CaptainSubmit } from "./CaptainSubmit";
import { RefereeOverview } from "./RefereeOverview";

export function ResultsWorkbench() {
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [overview, setOverview] = useState<ResultsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [activeTab, setActiveTab] = useState("captain");
  const [messageApi, contextHolder] = message.useMessage();

  const load = useCallback(async () => {
    setError("");
    try {
      const [courseData, overviewData] = await Promise.all([fetchCourse(), fetchResultsOverview()]);
      setCourse(courseData);
      setOverview(overviewData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载成绩数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (payload: SubmitPayload) => {
    setSubmitting(true);
    try {
      const { result } = await submitResult(payload);
      messageApi.success(
        result.status === "finished"
          ? `${result.teamName} 结算完成，成绩有效${result.rank ? `，当前第 ${result.rank} 名` : ""}。`
          : `${result.teamName} 记录已保留：${result.issueReason}`,
      );
      await load();
      setActiveTab("referee");
    } catch (err) {
      messageApi.error(err instanceof Error ? err.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (id: number, reason: string) => {
    setRevoking(true);
    try {
      await revokeResult(id, reason);
      messageApi.success("已撤销，队伍回到待结算，原成绩不再参与排名。");
      await load();
    } catch (err) {
      messageApi.error(err instanceof Error ? err.message : "撤销失败");
    } finally {
      setRevoking(false);
    }
  };

  if (loading) {
    return (
      <div className="workbench-loading">
        <Spin size="large" tip="加载线路与成绩数据…" />
      </div>
    );
  }

  if (error || !course || !overview) {
    return (
      <Result
        status="warning"
        title="成绩结算数据加载失败"
        subTitle={error || "后端服务暂不可用"}
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => void load()}>
            重新加载
          </Button>
        }
      />
    );
  }

  return (
    <section className="work-panel settlement-panel">
      {contextHolder}
      <Space className="settlement-header" align="center" style={{ justifyContent: "space-between", width: "100%" }}>
        <div>
          <Typography.Title level={3} style={{ margin: 0 }}>
            赛后成绩结算
          </Typography.Title>
          <Typography.Paragraph type="secondary" style={{ margin: "4px 0 0" }}>
            队长提交到点顺序与总用时，系统按线路校验点位与顺序；漏点或错序仍保留记录；裁判可撤销一次录错成绩。
          </Typography.Paragraph>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => void load()}>
          刷新
        </Button>
      </Space>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        style={{ marginTop: 8 }}
        items={[
          {
            key: "captain",
            label: (
              <span>
                <TeamOutlined /> 队长提交
              </span>
            ),
            children: (
              <CaptainSubmit
                course={course}
                overview={overview}
                submitting={submitting}
                onSubmit={(payload) => void handleSubmit(payload)}
              />
            ),
          },
          {
            key: "referee",
            label: (
              <span>
                <AuditOutlined /> 裁判总览
              </span>
            ),
            children: (
              <RefereeOverview overview={overview} revoking={revoking} onRevoke={handleRevoke} />
            ),
          },
        ]}
      />
    </section>
  );
}
