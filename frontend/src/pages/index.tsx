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
    refetchInterval: 1500,
  });
  const live = runtimeStats ?? data;
  const validStock = live?.valid_stock ?? data?.alive ?? 0;
  const scraped = live?.scraped ?? 0;
  const tested = live?.tested ?? data?.cycle_tested ?? 0;
  const valid = live?.valid ?? data?.cycle_valid ?? 0;
  const toTest = live ? Math.max(live.queued - live.tested, 0) : (data?.to_test ?? 0);
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
          hint={isLoading ? "Loading inventory" : "Raw proxies found this cycle"}
          label="Scraped"
          value={scraped}
        />
        <CardStat
          hint={`Alive stored: ${validStock}`}
          label="Valides stockes"
          value={validStock}
        />
        <CardStat
          hint={`Cycle phase: ${phase}`}
          label="A tester"
          value={toTest}
        />
        <CardStat
          hint={`Valid found this cycle: ${valid}`}
          label="Testes cycle"
          value={tested}
        />
        <CardStat
          hint="Across alive stored proxies"
          label="Latence moyenne"
          value={formatLatency(data?.avg_latency_ms)}
        />
      </div>
      <div className="mt-6 rounded-xl border border-line bg-panel p-6 shadow-glow">
        <h3 className="text-xl font-bold text-white">Mission loop</h3>
        <p className="mt-2 text-zinc-400">
          Scraped logs show raw candidates. Dashboard stats show what is
          actually stored in the database, split by validation status.
        </p>
        <p className="mt-3 text-sm text-zinc-500">
          GFP runs separately once at startup with a single tester:{" "}
          {runtimeStats?.gfp_tested ?? 0}/{runtimeStats?.gfp_queued ?? 0}{" "}
          checked, {runtimeStats?.gfp_valid ?? 0} valid.
        </p>
        <p className="mt-3 text-sm text-zinc-500">
          Distributed workers: {live?.worker_active ?? 0} active,{" "}
          {live?.worker_pending ?? 0} pending, {live?.worker_assigned ?? 0}{" "}
          assigned, {live?.worker_valid ?? 0} valid reported.
        </p>
      </div>
    </section>
  );
}
