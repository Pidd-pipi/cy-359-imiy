import { API_BASE_URL } from "../constants/app";
import type {
  CourseDetail,
  OverviewResponse,
  ResultsOverview,
  SubmitPayload,
  TeamResult,
} from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json", "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const message =
      payload && typeof payload === "object" && "message" in payload
        ? String((payload as { message: unknown }).message)
        : `请求失败（${response.status}）`;
    throw new Error(message);
  }
  return payload as T;
}

export function fetchOverview(): Promise<OverviewResponse> {
  return request<OverviewResponse>("/overview");
}

export function fetchCourse(): Promise<CourseDetail> {
  return request<CourseDetail>("/course");
}

export function fetchResultsOverview(): Promise<ResultsOverview> {
  return request<ResultsOverview>("/results/overview");
}

export function submitResult(payload: SubmitPayload): Promise<{ message: string; result: TeamResult }> {
  return request("/results/submit", { method: "POST", body: JSON.stringify(payload) });
}

export function revokeResult(id: number, reason: string): Promise<{ message: string; result: TeamResult }> {
  return request(`/results/${id}/revoke`, { method: "POST", body: JSON.stringify({ reason }) });
}
