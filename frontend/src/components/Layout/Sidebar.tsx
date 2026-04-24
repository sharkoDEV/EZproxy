import Link from "next/link";
import { useRouter } from "next/router";
import {
  Cog6ToothIcon,
  ServerStackIcon,
  Squares2X2Icon,
} from "@heroicons/react/24/outline";

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
        <div className="absolute bottom-12 left-3 right-3 rounded-lg border border-line bg-void/70 p-3 text-xs text-zinc-400">
          Live scrape, test and re-check loop without accounts or Docker.
        </div>
      ) : null}
    </aside>
  );
}
