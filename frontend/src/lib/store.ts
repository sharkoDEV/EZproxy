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
  last_error?: string | null;
  updated_at: string;
};

type AppState = {
  collapsed: boolean;
  theme: "dark" | "light";
  toast?: { message: string; tone: ToastTone };
  progress?: Progress;
  runtimeStats?: RuntimeStats;
  setCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: "dark" | "light") => void;
  showToast: (message: string, tone?: ToastTone) => void;
  clearToast: () => void;
  setProgress: (progress?: Progress) => void;
  setRuntimeStats: (stats?: RuntimeStats) => void;
};

export const useAppStore = create<AppState>((set) => ({
  collapsed: false,
  theme: "dark",
  setCollapsed: (collapsed) => set({ collapsed }),
  setTheme: (theme) => set({ theme }),
  showToast: (message, tone = "success") => set({ toast: { message, tone } }),
  clearToast: () => set({ toast: undefined }),
  setProgress: (progress) => set({ progress }),
  setRuntimeStats: (runtimeStats) => set({ runtimeStats }),
}));
