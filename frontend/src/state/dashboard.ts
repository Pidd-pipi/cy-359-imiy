import { localFeatures, localKpis, operationRecords } from "../data/workbench";
import type { OverviewResponse } from "../types";
import { APP_CODE, APP_NAME } from "../constants/app";

export function createFallbackOverview(): OverviewResponse {
  return {
    appName: APP_NAME,
    appCode: APP_CODE,
    description: "面向户外运动爱好者，提供定向越野线路设计、团队报名和积分排名的活动平台。",
    features: localFeatures,
    kpis: localKpis,
    records: operationRecords,
  };
}
