import { API_BASE_URL } from "../constants/app";
import type {
  OverviewResponse,
  RouteInfo,
  SubmitResultPayload,
  TeamResultRecord,
} from "../types";

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function parseJson(response: Response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    ...init,
  });

  const payload = await parseJson(response);
  if (!response.ok) {
    const message = payload?.message ?? `请求失败（${response.status}）`;
    throw new ApiRequestError(response.status, payload?.error ?? "error", message);
  }
  return payload as T;
}

export function fetchRoutes(): Promise<{ routes: RouteInfo[] }> {
  return request("/routes");
}

export function fetchOverview(routeId?: number): Promise<OverviewResponse> {
  const query = routeId ? `?route=${routeId}` : "";
  return request<OverviewResponse>(`/overview${query}`);
}

export function submitResult(
  payload: SubmitResultPayload
): Promise<{ record: TeamResultRecord }> {
  return request("/results/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function revokeResult(
  resultId: number,
  reason = ""
): Promise<{ record: TeamResultRecord }> {
  return request(`/results/${resultId}/revoke`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
