import { useQuery } from "@tanstack/react-query";
import { CardStat } from "@/components/CardStat";
import { fetchProxyStats } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatLatency } from "@/utils/helpers";

export default function Dashboard() {
  const runtimeStats = useAppStore((state) => state.runtimeStats);
  const { data, isLoading } = useQuery({
    queryKey: ["proxies", "stats"],
    queryFn: fetchProxyStats,
    refetchInterval: 5000,
  });
  const validStock = runtimeStats?.valid_stock ?? data?.alive ?? 0;
  const toTest = runtimeStats
    ? Math.max(runtimeStats.queued - runtimeStats.tested, 0)
    : (data?.to_test ?? 0);
  const phase = runtimeStats?.phase ?? data?.phase ?? "idle";

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
          value={validStock}
        />
        <CardStat
          hint={`Cycle phase: ${phase}`}
          label="A tester"
          value={toTest}
        />
        <CardStat
          hint="Across alive proxies"
          label="Latence moyenne"
          value={formatLatency(data?.avg_latency_ms)}
        />
        <CardStat
          hint={`${data?.unknown ?? 0} still waiting for validation`}
          label="Dead / unknown"
          value={`${data?.dead ?? 0} / ${data?.unknown ?? 0}`}
        />
      </div>
      <div className="mt-6 rounded-xl border border-line bg-panel p-6 shadow-glow">
        <h3 className="text-xl font-bold text-white">Mission loop</h3>
        <p className="mt-2 text-zinc-400">
          Scraped logs show raw candidates. Dashboard stats show what is
          actually stored in the database, split by validation status.
        </p>
      </div>
    </section>
  );
}
