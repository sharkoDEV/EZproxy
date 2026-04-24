import { useQuery } from "@tanstack/react-query";
import { CardStat } from "@/components/CardStat";
import { fetchProxies } from "@/lib/api";
import { formatLatency } from "@/utils/helpers";

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["proxies", "dashboard"],
    queryFn: () => fetchProxies({ page_size: 500 }),
  });
  const proxies = data?.items ?? [];
  const alive = proxies.filter((proxy) => proxy.status === "alive");
  const dead = proxies.filter((proxy) => proxy.status === "dead");
  const avgLatency =
    alive.length > 0
      ? alive.reduce((sum, proxy) => sum + (proxy.latency_ms ?? 0), 0) /
        alive.length
      : undefined;

  return (
    <section className="h-full overflow-auto">
      <div className="mb-6">
        <p className="text-sm uppercase tracking-[0.35em] text-neon">
          Dashboard
        </p>
        <h2 className="mt-2 text-4xl font-black text-white">
          Proxy telemetry, but make it nocturnal.
        </h2>
        <p className="mt-3 max-w-2xl text-zinc-400">
          Scrape public sources, test live reachability, and watch the fleet
          pulse in real time.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <CardStat
          hint={isLoading ? "Loading inventory" : "Stored proxy records"}
          label="Total proxies"
          value={data?.total ?? 0}
        />
        <CardStat
          hint="Reachable during last test"
          label="Actifs"
          value={alive.length}
        />
        <CardStat
          hint="Across alive proxies"
          label="Latence moyenne"
          value={formatLatency(avgLatency)}
        />
        <CardStat
          hint="Dead or timed out"
          label="Dernières erreurs"
          value={dead.length}
        />
      </div>
      <div className="mt-6 rounded-xl border border-line bg-panel p-6 shadow-glow">
        <h3 className="text-xl font-bold text-white">Mission loop</h3>
        <p className="mt-2 text-zinc-400">
          The backend re-check worker wakes up on the configured interval and
          retests stale proxies. The table page listens to Socket.IO for
          progress and status events.
        </p>
      </div>
    </section>
  );
}
