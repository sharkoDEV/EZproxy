import Link from "next/link";
import { useRouter } from "next/router";
import {
  BoltIcon,
  Cog6ToothIcon,
  ServerStackIcon,
  Squares2X2Icon,
} from "@heroicons/react/24/outline";
import { API_BASE_URL } from "@/lib/api";
import { SOCKET_BASE_URL } from "@/lib/socket";
import { useAppStore } from "@/lib/store";

const items = [
  { href: "/", label: "Dashboard", icon: Squares2X2Icon },
  { href: "/proxies", label: "Proxies", icon: ServerStackIcon },
  { href: "/settings", label: "Settings", icon: Cog6ToothIcon },
];

type SidebarProps = {
  collapsed: boolean;
};

export function Sidebar({ collapsed }: SidebarProps) {
  const router = useRouter();
  const apiConnected = useAppStore((state) => state.apiConnected);
  const connectionError = useAppStore((state) => state.connectionError);
  const lastApiCheck = useAppStore((state) => state.lastApiCheck);
  const socketConnected = useAppStore((state) => state.socketConnected);
  const allConnected = apiConnected && socketConnected;

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-20 border-r border-line bg-panel py-20 transition-all duration-200 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <nav className="space-y-2 px-3">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            router.pathname === item.href ||
            router.pathname.startsWith(`${item.href}/`);
          return (
            <Link
              aria-label={item.label}
              className={`flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-semibold transition duration-200 ${
                active
                  ? "bg-neon text-void"
                  : "text-zinc-300 hover:bg-white/5 hover:text-magenta"
              }`}
              href={item.href}
              key={item.href}
            >
              <Icon className="h-6 w-6 shrink-0" />
              {!collapsed ? <span>{item.label}</span> : null}
            </Link>
          );
        })}
      </nav>
      {!collapsed ? (
        <div className="absolute bottom-12 left-3 right-3 space-y-3">
          <div
            className={`rounded-lg border p-3 text-xs ${
              allConnected
                ? "border-neon bg-neon/5 text-neon"
                : "border-magenta bg-magenta/5 text-magenta"
            }`}
          >
            <div className="mb-3 flex items-center gap-2 font-black uppercase tracking-[0.25em]">
              <BoltIcon className="h-4 w-4" />
              Backend {allConnected ? "connected" : "sync issue"}
            </div>
            <div className="space-y-2 text-zinc-300">
              <div className="flex items-center justify-between">
                <span>API</span>
                <span className={apiConnected ? "text-neon" : "text-magenta"}>
                  {apiConnected ? "OK" : "KO"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Socket</span>
                <span
                  className={socketConnected ? "text-neon" : "text-magenta"}
                >
                  {socketConnected ? "OK" : "KO"}
                </span>
              </div>
              <div className="truncate text-[10px] text-zinc-500">
                API: {API_BASE_URL}
              </div>
              <div className="truncate text-[10px] text-zinc-500">
                WS: {SOCKET_BASE_URL}/ws/proxies
              </div>
              {lastApiCheck ? (
                <div className="text-[10px] text-zinc-500">
                  Last check: {lastApiCheck}
                </div>
              ) : null}
              {!apiConnected && connectionError ? (
                <div className="truncate text-[10px] text-magenta">
                  {connectionError}
                </div>
              ) : null}
            </div>
          </div>
          <div className="rounded-lg border border-line bg-void/70 p-3 text-xs text-zinc-400">
            Live scrape, test and re-check loop without accounts or Docker.
          </div>
        </div>
      ) : null}
    </aside>
  );
}
