import type { PropsWithChildren } from "react";
import { useEffect, useState } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Footer } from "./Footer";
import { AdminLoginModal } from "../AdminLoginModal";
import { Toast } from "../Toast";
import { fetchAdminMe } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export function Layout({ children }: PropsWithChildren) {
  const [adminOpen, setAdminOpen] = useState(false);
  const collapsed = useAppStore((state) => state.collapsed);
  const theme = useAppStore((state) => state.theme);
  const adminToken = useAppStore((state) => state.adminToken);
  const socketConnected = useAppStore((state) => state.socketConnected);
  const setCollapsed = useAppStore((state) => state.setCollapsed);
  const setAdminToken = useAppStore((state) => state.setAdminToken);
  const setTheme = useAppStore((state) => state.setTheme);
  const showToast = useAppStore((state) => state.showToast);

  useEffect(() => {
    const stored = window.localStorage.getItem("ezproxy-theme");
    if (stored === "dark" || stored === "light") {
      setTheme(stored);
    }
    const token = window.localStorage.getItem("ezproxy-token");
    if (token) {
      setAdminToken(token);
    }
  }, [setAdminToken, setTheme]);

  useEffect(() => {
    if (!adminToken) {
      return;
    }
    fetchAdminMe().catch(() => {
      setAdminToken(undefined);
      showToast("Admin session expired", "error");
    });
  }, [adminToken, setAdminToken, showToast]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("ezproxy-theme", theme);
  }, [theme]);

  return (
    <div className="scanline min-h-screen bg-void text-ink">
      <Header
        collapsed={collapsed}
        isAdmin={Boolean(adminToken)}
        socketConnected={socketConnected}
        theme={theme}
        onLogoutAdmin={() => {
          setAdminToken(undefined);
          showToast("Admin disconnected", "info");
        }}
        onOpenAdmin={() => setAdminOpen(true)}
        onToggleSidebar={() => setCollapsed(!collapsed)}
        onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
      />
      <Sidebar collapsed={collapsed} />
      <main
        className={`fixed bottom-10 top-16 overflow-hidden p-6 transition-all duration-200 ${
          collapsed ? "left-20 right-0" : "left-64 right-0"
        }`}
      >
        {children}
      </main>
      <Footer collapsed={collapsed} />
      <AdminLoginModal open={adminOpen} onClose={() => setAdminOpen(false)} />
      <Toast />
    </div>
  );
}
