import { create } from "zustand";

type ToastTone = "success" | "error" | "info";

type Progress = {
  tested: number;
  total: number;
  valid: number;
};

export type RuntimeStats = {
  phase: string;
  cycle_active: boolean;
  cycle_started_at?: string | null;
  source?: string | null;
  scraped: number;
  queued: number;
  tested: number;
  valid: number;
  stored: number;
  valid_stock: number;
  total_stock: number;
  gfp_active: boolean;
  gfp_scraped: number;
  gfp_queued: number;
  gfp_tested: number;
  gfp_valid: number;
  gfp_stored: number;
  worker_pending: number;
  worker_assigned: number;
  worker_active: number;
  worker_reported: number;
  worker_valid: number;
  worker_stored: number;
  last_error?: string | null;
  updated_at: string;
};

type AppState = {
  collapsed: boolean;
  theme: "dark" | "light";
  adminToken?: string;
  apiConnected: boolean;
  lastApiCheck?: string;
  connectionError?: string;
  socketConnected: boolean;
  toast?: { message: string; tone: ToastTone };
  progress?: Progress;
  runtimeStats?: RuntimeStats;
  setCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: "dark" | "light") => void;
  setAdminToken: (token?: string) => void;
  setApiStatus: (connected: boolean, error?: string) => void;
  setSocketConnected: (connected: boolean) => void;
  showToast: (message: string, tone?: ToastTone) => void;
  clearToast: () => void;
  setProgress: (progress?: Progress) => void;
  setRuntimeStats: (stats?: RuntimeStats) => void;
};

export const useAppStore = create<AppState>((set) => ({
  collapsed: false,
  theme: "dark",
  apiConnected: false,
  socketConnected: false,
  setCollapsed: (collapsed) => set({ collapsed }),
  setTheme: (theme) => set({ theme }),
  setAdminToken: (adminToken) => {
    if (typeof window !== "undefined") {
      if (adminToken) {
        window.localStorage.setItem("ezproxy-token", adminToken);
      } else {
        window.localStorage.removeItem("ezproxy-token");
      }
    }
    set({ adminToken });
  },
  setApiStatus: (apiConnected, connectionError) =>
    set({
      apiConnected,
      connectionError,
      lastApiCheck: new Date().toLocaleTimeString(),
    }),
  setSocketConnected: (socketConnected) => set({ socketConnected }),
  showToast: (message, tone = "success") => set({ toast: { message, tone } }),
  clearToast: () => set({ toast: undefined }),
  setProgress: (progress) => set({ progress }),
  setRuntimeStats: (runtimeStats) => set({ runtimeStats }),
}));
