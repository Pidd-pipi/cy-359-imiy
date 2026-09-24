export interface FeatureItem {
  id: number;
  title: string;
  description: string;
  status: string;
  metric: string;
}

export interface KpiItem {
  label: string;
  value: string;
  trend: string;
  tone: string;
}

export interface OperationRecord {
  key: string;
  name: string;
  owner: string;
  status: string;
  metric: string;
  priority: string;
}

export interface OverviewResponse {
  appName: string;
  appCode: string;
  description: string;
  features: FeatureItem[];
  kpis: KpiItem[];
  records: OperationRecord[];
}

// ---- 赛后成绩结算 ----

export type ResultStatus = "pending" | "finished" | "incomplete" | "revoked";

export interface TeamResult {
  id: number | null;
  teamName: string;
  courseName: string;
  sequence: string[];
  totalSeconds: number | null;
  totalTime: string;
  status: ResultStatus;
  statusLabel: string;
  issueReason: string;
  rank: number | null;
  revokeCount: number;
  revocable: boolean;
  submittedAt: string | null;
  settledAt: string | null;
  revokedAt: string | null;
}

export interface OverviewStat {
  key: ResultStatus;
  label: string;
  value: number;
}

export interface CourseDetail {
  name: string;
  checkpoints: string[];
  teams: string[];
}

export interface ResultsOverview {
  course: { name: string; checkpoints: string[] };
  teams: string[];
  stats: OverviewStat[];
  teamsResults: TeamResult[];
  ranking: TeamResult[];
  revokedResults: TeamResult[];
}

export interface SubmitPayload {
  teamName: string;
  sequence: string[];
  totalTime: string;
}
