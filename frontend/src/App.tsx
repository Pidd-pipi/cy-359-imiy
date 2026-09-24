import { useCallback, useEffect, useState } from "react";
import {
  App as AntApp,
  Badge,
  Button,
  ConfigProvider,
  Layout,
  Tabs,
  Typography,
  theme,
} from "antd";
import { ApiOutlined } from "@ant-design/icons";
import {
  ApiRequestError,
  fetchOverview,
  fetchRoutes,
  revokeResult,
  submitResult,
} from "./api/client";
import { APP_CODE, APP_NAME, APP_THEME } from "./constants/app";
import { REQUEST_MESSAGES } from "./constants/messages";
import type {
  OverviewResponse,
  RouteInfo,
  SubmitResultPayload,
  TeamResultRecord,
} from "./types";
import { SubmitForm } from "./components/SubmitForm";
import { OverviewBoard } from "./components/OverviewBoard";

const { Header, Content } = Layout;

const REFRESH_INTERVAL_MS = 20_000;

export default function App() {
  const { message } = AntApp.useApp();
  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [activeTab, setActiveTab] = useState("submit");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [revokingId, setRevokingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadRoutes = useCallback(async () => {
    try {
      const payload = await fetchRoutes();
      setRoutes(payload.routes);
    } catch {
      setRoutes([]);
    }
  }, []);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await fetchOverview();
      setOverview(payload);
      setError(null);
    } catch {
      setError(REQUEST_MESSAGES.overviewFallback);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRoutes();
    loadOverview();
  }, [loadRoutes, loadOverview]);

  // 裁判总览页轮询刷新
  useEffect(() => {
    if (activeTab !== "overview") {
      return;
    }
    const timer = window.setInterval(loadOverview, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [activeTab, loadOverview]);

  const handleSubmit = async (payload: SubmitResultPayload) => {
    if (payload.totalSeconds <= 0) {
      message.warning("总用时必须大于 0，请重新填写。");
      return;
    }
    setSubmitting(true);
    try {
      const { record } = await submitResult(payload);
      if (record.status === "completed") {
        message.success(`${REQUEST_MESSAGES.submitSuccess}：成绩有效，当前第 ${record.rank} 名。`);
      } else {
        message.warning(record.resultNote);
      }
      setActiveTab("overview");
      await loadOverview();
    } catch (err) {
      const text =
        err instanceof ApiRequestError && err.status === 409
          ? REQUEST_MESSAGES.duplicateSubmit
          : err instanceof Error
            ? err.message
            : "提交失败，请稍后重试";
      message.error(text);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (record: TeamResultRecord) => {
    setRevokingId(record.id);
    try {
      await revokeResult(record.id);
      message.success(REQUEST_MESSAGES.revokeSuccess);
      await Promise.all([loadOverview(), loadRoutes()]);
    } catch (err) {
      message.error(err instanceof Error ? err.message : "撤销失败，请稍后重试");
    } finally {
      setRevokingId(null);
    }
  };

  const pendingCount = overview?.totals.pendingCount ?? 0;

  const tabItems = [
    {
      key: "submit",
      label: "成绩提交",
      children: (
        <div className="submit-layout">
          <SubmitForm routes={routes} submitting={submitting} onSubmit={handleSubmit} />
          <div className="rules-panel">
            <Typography.Title level={4}>结算规则</Typography.Title>
            <ul>
              <li>队长提交队名、到点顺序和总用时，系统按线路规定顺序校验。</li>
              <li>点位齐全且顺序一致：成绩有效，按总用时升序排名。</li>
              <li>漏点或顺序错误：比赛记录仍然保留，成绩栏注明未完成原因，不参与排名。</li>
              <li>同一队伍重复提交：只保留先完成的一份，后续提交被拒绝。</li>
              <li>裁判可对录错成绩撤销一次；撤销后队伍回到待结算，可重新提交。</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      key: "overview",
      label: (
        <Badge count={pendingCount} size="small" offset={[10, -2]}>
          裁判总览
        </Badge>
      ),
      children: (
        <OverviewBoard
          overview={overview}
          loading={loading}
          error={error}
          revokingId={revokingId}
          onReload={loadOverview}
          onRevoke={handleRevoke}
        />
      ),
    },
  ];

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: APP_THEME.accent,
          colorText: APP_THEME.ink,
          colorBgBase: APP_THEME.paper,
          borderRadius: 8,
        },
      }}
    >
      <AntApp>
        <Layout className="app-shell">
          <Header className="topbar">
            <div className="brand-block">
              <span className="brand-code">{APP_CODE}</span>
              <h1 className="brand-title">
                {APP_NAME} · 赛后成绩结算
              </h1>
            </div>
            <Button type="primary" icon={<ApiOutlined />} href={REQUEST_MESSAGES.healthPath}>
              API Health
            </Button>
          </Header>
          <Content className="workspace">
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabItems}
              destroyInactiveTabPane
            />
          </Content>
        </Layout>
      </AntApp>
    </ConfigProvider>
  );
}
