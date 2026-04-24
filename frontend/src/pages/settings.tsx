import { CardStat } from "@/components/CardStat";

export default function Settings() {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  const socketUrl =
    process.env.NEXT_PUBLIC_SOCKET_URL ?? "http://localhost:8000";

  return (
    <section className="h-full overflow-auto">
      <div className="mb-6">
        <p className="text-sm uppercase tracking-[0.35em] text-neon">
          Settings
        </p>
        <h2 className="mt-1 text-3xl font-black text-white">
          Local configuration
        </h2>
        <p className="mt-3 max-w-2xl text-zinc-400">
          Runtime proxy rules live in the root <code>config.json</code>.
          Frontend endpoints come from environment variables.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <CardStat hint="NEXT_PUBLIC_API_URL" label="API" value={apiUrl} />
        <CardStat
          hint="NEXT_PUBLIC_SOCKET_URL"
          label="Socket"
          value={socketUrl}
        />
      </div>
      <div className="mt-6 rounded-xl border border-line bg-panel p-6 text-sm text-zinc-300">
        <p className="font-bold text-white">Keyboard shortcuts</p>
        <p className="mt-2">
          Use tab focus to move through controls. Focus rings are neon green for
          visibility.
        </p>
      </div>
    </section>
  );
}
