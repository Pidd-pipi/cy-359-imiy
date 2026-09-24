export type ResultStatus = "completed" | "incomplete" | "revoked";

export interface RouteInfo {
  id: number;
  name: string;
  description: string;
  checkpointSequence: string[];
  checkpointCount: number;
}

export interface TeamResultRecord {
  id: number;
  routeId: number;
  teamName: string;
  submittedSequence: string[];
  totalSeconds: number;
  duration: string;
  status: ResultStatus;
  statusLabel: string;
  issues: string[];
  issueLabels: string[];
  resultNote: string;
  completedAt: string;
  revokedAt: string | null;
  revokeReason: string;
  rank: number | null;
  previousStatus?: ResultStatus;
  previousStatusLabel?: string;
}

export interface RouteOverviewSummary {
  settledCount: number;
  completedCount: number;
  incompleteCount: number;
  pendingCount: number;
  revokedCount: number;
}

export interface RouteOverview {
  route: RouteInfo;
  records: TeamResultRecord[];
  pendingTeams: string[];
  revokedRecords: TeamResultRecord[];
  summary: RouteOverviewSummary;
}

export interface OverviewTotals {
  teamCount: number;
  settledCount: number;
  completedCount: number;
  incompleteCount: number;
  pendingCount: number;
  revokedCount: number;
}

export interface OverviewResponse {
  routes: RouteOverview[];
  totals: OverviewTotals;
}

export interface SubmitResultPayload {
  routeId: number;
  teamName: string;
  submittedSequence: string[];
  totalSeconds: number;
}
