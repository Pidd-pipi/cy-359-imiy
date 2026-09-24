import { useEffect, useState } from "react";
import { Button, ConfigProvider, Layout, Typography, theme } from "antd";
import { ApiOutlined } from "@ant-design/icons";
import { fetchOverview } from "./api/client";
import { APP_CODE, APP_NAME, APP_THEME } from "./constants/app";
import { REQUEST_MESSAGES } from "./constants/messages";
import { createFallbackOverview } from "./state/dashboard";
import type { OverviewResponse } from "./types";
import { FeatureStrip } from "./components/FeatureStrip";
import { MetricGrid } from "./components/MetricGrid";
import { OperationsTable } from "./components/OperationsTable";

const { Header, Content } = Layout;

export default function App() {
  const [overview, setOverview] = useState<OverviewResponse>(createFallbackOverview());
  const [notice, setNotice] = useState(REQUEST_MESSAGES.overviewFallback);

  useEffect(() => {
    fetchOverview()
      .then((payload) => {
        setOverview(payload);
        setNotice("后端服务已联通，当前展示实时接口数据。");
      })
      .catch(() => setNotice(REQUEST_MESSAGES.overviewFallback));
  }, []);

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
      <Layout className="app-shell">
        <Header className="topbar">
          <div className="brand-block">
            <span className="brand-code">{APP_CODE}</span>
            <h1 className="brand-title">{APP_NAME}</h1>
          </div>
          <Button type="primary" icon={<ApiOutlined />} href={REQUEST_MESSAGES.healthPath}>API Health</Button>
        </Header>
        <Content className="workspace">
          <section className="lead-grid">
            <article className="hero-panel">
              <span className="pill">{notice}</span>
              <Typography.Title level={2}>{overview.appName}</Typography.Title>
              <p>{overview.description}</p>
            </article>
            <MetricGrid items={overview.kpis} />
          </section>
          <FeatureStrip items={overview.features} />
          <section className="work-panel">
            <Typography.Title level={3}>运营任务流</Typography.Title>
            <OperationsTable records={overview.records} />
          </section>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}
