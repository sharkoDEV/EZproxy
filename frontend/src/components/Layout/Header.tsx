import { Bars3Icon, MoonIcon, SunIcon } from "@heroicons/react/24/outline";
import { Button } from "../Button";

type HeaderProps = {
  collapsed: boolean;
  theme: "dark" | "light";
  isAdmin: boolean;
  onToggleSidebar: () => void;
  onToggleTheme: () => void;
  onOpenAdmin: () => void;
  onLogoutAdmin: () => void;
};

export function Header({
  collapsed,
  isAdmin,
  onLogoutAdmin,
  onOpenAdmin,
  onToggleSidebar,
  onToggleTheme,
  theme,
}: HeaderProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-30 flex h-16 items-center justify-between border-b border-line bg-void/95 px-6 shadow-md backdrop-blur">
      <div className="flex items-center gap-4">
        <Button
          aria-label="Toggle sidebar"
          className="px-3"
          variant="ghost"
          onClick={onToggleSidebar}
        >
          <Bars3Icon className="h-5 w-5" />
        </Button>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-neon">
            ezProxy
          </p>
          <h1 className="text-lg font-black text-white">
            {collapsed ? "Control" : "Proxy Control Room"}
          </h1>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Button
          aria-label="Toggle theme"
          variant="secondary"
          onClick={onToggleTheme}
        >
          {theme === "dark" ? (
            <MoonIcon className="h-5 w-5" />
          ) : (
            <SunIcon className="h-5 w-5" />
          )}
        </Button>
        <Button
          aria-label={isAdmin ? "Logout admin" : "Login admin"}
          variant={isAdmin ? "primary" : "ghost"}
          onClick={isAdmin ? onLogoutAdmin : onOpenAdmin}
        >
          {isAdmin ? "Admin ON" : "Admin"}
        </Button>
        <div className="grid h-10 w-10 place-items-center rounded-full border border-neon bg-panel text-sm font-bold text-neon">
          EZ
        </div>
      </div>
    </header>
  );
}
