import { useEffect } from "react";
import { useAppStore } from "@/lib/store";

export function Toast() {
  const toast = useAppStore((state) => state.toast);
  const clearToast = useAppStore((state) => state.clearToast);

  useEffect(() => {
    if (!toast) {
      return;
    }
    const timeout = window.setTimeout(clearToast, 3200);
    return () => window.clearTimeout(timeout);
  }, [clearToast, toast]);

  if (!toast) {
    return null;
  }

  const border = toast.tone === "error" ? "border-magenta" : "border-neon";

  return (
    <div
      className={`fixed right-4 top-4 z-50 rounded-md border ${border} bg-panel p-3 text-sm shadow-glow`}
    >
      {toast.message}
    </div>
  );
}
