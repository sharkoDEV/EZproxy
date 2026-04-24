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
  avg_latency_ms?: number | null;
};

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  timeout: 15000,
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

export async function fetchProxyIds(
  params?: Record<string, string | number | boolean | undefined>,
) {
  const { data } = await api.get<{ ids: number[]; total: number }>(
    "/proxies/ids",
    { params },
  );
  return data;
}

export async function fetchProxy(id: string | number) {
  const { data } = await api.get<ProxyRecord>(`/proxies/${id}`);
  return data;
}
