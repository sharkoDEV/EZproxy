import type { PropsWithChildren } from "react";
import { useEffect } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Footer } from "./Footer";
import { Toast } from "../Toast";
import { useAppStore } from "@/lib/store";

export function Layout({ children }: PropsWithChildren) {
  const collapsed = useAppStore((state) => state.collapsed);
  const theme = useAppStore((state) => state.theme);
  const setCollapsed = useAppStore((state) => state.setCollapsed);
  const setTheme = useAppStore((state) => state.setTheme);

  useEffect(() => {
    const stored = window.localStorage.getItem("ezproxy-theme");
    if (stored === "dark" || stored === "light") {
      setTheme(stored);
    }
  }, [setTheme]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("ezproxy-theme", theme);
  }, [theme]);

  return (
    <div className="scanline min-h-screen bg-void text-ink">
      <Header
        collapsed={collapsed}
        theme={theme}
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
      <Toast />
    </div>
  );
}
