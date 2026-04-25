import axios from "axios";

export type ProxyRecord = {
  id: number;
  ip: string;
  port: number;
  type: string;
  country?: string | null;
  anonymity?: string | null;
  latency_ms?: number | null;
  last_checked?: string | null;
  status: "alive" | "dead" | "unknown" | string;
  is_manual: boolean;
};

export type ProxyCreateInput = {
  ip: string;
  port: number;
  type: string;
  country?: string;
  anonymity?: string;
  test_now: boolean;
};

export type ProxyBulkCreateInput = {
  proxies: string;
  type: string;
  country?: string;
  anonymity?: string;
  test_now: boolean;
};

export type ProxyBulkResult = {
  added: number;
  updated: number;
  skipped: number;
  total_parsed: number;
};

export type ProxyListResponse = {
  items: ProxyRecord[];
  total: number;
  page: number;
  page_size: number;
};

export type ProxyStats = {
  total: number;
  alive: number;
  dead: number;
  unknown: number;
  to_test: number;
  cycle_tested: number;
  cycle_valid: number;
  cycle_active: boolean;
  phase: string;
  source?: string | null;
  scraped: number;
  queued: number;
  tested: number;
  valid: number;
  stored: number;
  valid_stock: number;
  total_stock: number;
  worker_pending: number;
  worker_assigned: number;
  worker_active: number;
  worker_reported: number;
  worker_valid: number;
  worker_stored: number;
  avg_latency_ms?: number | null;
};

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("ezproxy-token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export async function fetchProxies(
  params?: Record<string, string | number | boolean | undefined>,
) {
  const { data } = await api.get<ProxyListResponse>("/proxies", { params });
  return data;
}

export async function fetchProxyStats() {
  const { data } = await api.get<ProxyStats>("/proxies/stats");
  return data;
}

export async function fetchHealth() {
  const { data } = await api.get<{ status: string; service: string }>(
    "/health",
    { timeout: 2500 },
  );
  return data;
}

export async function fetchProxy(id: string | number) {
  const { data } = await api.get<ProxyRecord>(`/proxies/${id}`);
  return data;
}

export async function loginAdmin(password: string) {
  const { data } = await api.post<{ authenticated: boolean; token: string }>(
    "/admin/login",
    { password },
  );
  return data;
}

export async function fetchAdminMe() {
  const { data } = await api.get<{ authenticated: boolean }>("/admin/me");
  return data;
}

export async function createProxy(payload: ProxyCreateInput) {
  const { data } = await api.post<ProxyRecord>("/proxies", payload);
  return data;
}

export async function createProxyBulk(payload: ProxyBulkCreateInput) {
  const { data } = await api.post<ProxyBulkResult>("/proxies/bulk", payload);
  return data;
}
