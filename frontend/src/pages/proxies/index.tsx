import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AddProxyModal } from "@/components/AddProxyModal";
import { Button } from "@/components/Button";
import { FilterBar } from "@/components/FilterBar";
import { CardStat } from "@/components/CardStat";
import { ProgressBar } from "@/components/ProgressBar";
import { ProxyTable } from "@/components/ProxyTable";
import { fetchProxies } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function ProxiesPage() {
  const progress = useAppStore((state) => state.progress);
  const runtimeStats = useAppStore((state) => state.runtimeStats);
  const adminToken = useAppStore((state) => state.adminToken);
  const socketConnected = useAppStore((state) => state.socketConnected);
  const showToast = useAppStore((state) => state.showToast);
  const [addOpen, setAddOpen] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    type: "",
    country: "",
    anonymity: "",
  });

  const params = useMemo(
    () => ({
      page_size: 500,
      search: filters.search || undefined,
      type: filters.type || undefined,
      country: filters.country || undefined,
      anonymity: filters.anonymity || undefined,
    }),
    [filters],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["proxies", params],
    queryFn: () => fetchProxies(params),
    refetchInterval: 2500,
  });

  function exportFile(format: "txt" | "csv") {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/proxies/export?format=${format}`,
      "_blank",
    );
  }

  const proxies = data?.items ?? [];
  const toTest = runtimeStats
    ? Math.max(runtimeStats.queued - runtimeStats.tested, 0)
    : 0;

  return (
    <section className="flex h-full flex-col gap-4 overflow-hidden">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.35em] text-neon">
            Proxy Fleet
          </p>
          <h2 className="mt-1 text-3xl font-black text-white">
            Scrape, test, re-check, export.
          </h2>
        </div>
        <div className="rounded-lg border border-line bg-panel px-4 py-2 text-sm text-zinc-400">
          {socketConnected
            ? "Live Socket.IO sync is connected."
            : "Reconnecting live sync, polling backup is active."}
        </div>
      </div>
      <div className="flex items-center justify-between gap-3 rounded-lg border border-line bg-panel p-3">
        <div>
          <p className="text-sm font-bold text-white">Manual admin proxies</p>
          <p className="text-xs text-zinc-400">
            Added proxies are pinned in the database and survive backend restart.
          </p>
        </div>
        <Button
          variant={adminToken ? "primary" : "ghost"}
          onClick={() => {
            if (!adminToken) {
              showToast("Login as admin first", "error");
              return;
            }
            setAddOpen(true);
          }}
        >
          Add proxy
        </Button>
      </div>
      <FilterBar
        values={filters}
        onChange={setFilters}
        onExport={exportFile}
      />
      <div className="grid gap-3 md:grid-cols-4">
        <CardStat
          label="Valides live"
          value={runtimeStats?.valid_stock ?? "sync"}
          hint="Alive stored in database"
        />
        <CardStat
          label="A tester"
          value={toTest}
          hint="Remaining in current automatic cycle"
        />
        <CardStat
          label="Testes cycle"
          value={runtimeStats?.tested ?? 0}
          hint={`Valid this cycle: ${runtimeStats?.valid ?? 0}`}
        />
        <CardStat
          label="Phase"
          value={runtimeStats?.phase ?? "idle"}
          hint={
            runtimeStats?.source
              ? `Source: ${runtimeStats.source}`
              : "Automatic worker"
          }
        />
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <CardStat
          label="GFP worker"
          value={runtimeStats?.gfp_active ? "running" : "done"}
          hint="Separate one-shot worker, 1 tester"
        />
        <CardStat
          label="GFP a tester"
          value={
            runtimeStats
              ? Math.max(runtimeStats.gfp_queued - runtimeStats.gfp_tested, 0)
              : 0
          }
          hint={`Scraped: ${runtimeStats?.gfp_scraped ?? 0}`}
        />
        <CardStat
          label="GFP testes"
          value={runtimeStats?.gfp_tested ?? 0}
          hint={`Valid: ${runtimeStats?.gfp_valid ?? 0}`}
        />
        <CardStat
          label="GFP stockes"
          value={runtimeStats?.gfp_stored ?? 0}
          hint="Alive proxies added from GFP"
        />
      </div>
      {progress ? <ProgressBar {...progress} /> : null}
      <ProxyTable loading={isLoading} proxies={proxies} />
      <AddProxyModal open={addOpen} onClose={() => setAddOpen(false)} />
    </section>
  );
}
