import { create } from "zustand";

type ToastTone = "success" | "error" | "info";

type Progress = {
  tested: number;
  total: number;
  valid: number;
};

type AppState = {
  collapsed: boolean;
  theme: "dark" | "light";
  toast?: { message: string; tone: ToastTone };
  progress?: Progress;
  setCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: "dark" | "light") => void;
  showToast: (message: string, tone?: ToastTone) => void;
  clearToast: () => void;
  setProgress: (progress?: Progress) => void;
};

export const useAppStore = create<AppState>((set) => ({
  collapsed: false,
  theme: "dark",
  setCollapsed: (collapsed) => set({ collapsed }),
  setTheme: (theme) => set({ theme }),
  showToast: (message, tone = "success") => set({ toast: { message, tone } }),
  clearToast: () => set({ toast: undefined }),
  setProgress: (progress) => set({ progress }),
}));
