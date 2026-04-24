import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/Button";
import { FilterBar } from "@/components/FilterBar";
import { ProgressBar } from "@/components/ProgressBar";
import { ProxyTable } from "@/components/ProxyTable";
import { api, fetchProxies, fetchProxyIds } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function ProxiesPage() {
  const queryClient = useQueryClient();
  const showToast = useAppStore((state) => state.showToast);
  const progress = useAppStore((state) => state.progress);
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
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["proxies"] });
  const scrapeMutation = useMutation({
    mutationFn: () => api.post("/proxies/scrape"),
    onSuccess: () => {
      showToast("Sources scraped");
      invalidate();
    },
    onError: () => showToast("Scrape failed", "error"),
  });
  const batchMutation = useMutation({
    mutationFn: async () => {
      const { ids } = await fetchProxyIds(params);
      return api.post("/proxies/test-batch", { ids });
    },
    onSuccess: () => {
      showToast("Batch test complete");
      invalidate();
    },
  });

  function exportFile(format: "txt" | "csv") {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/proxies/export?format=${format}`,
      "_blank",
    );
  }

  const proxies = data?.items ?? [];

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
        <div className="flex gap-2">
          <Button
            disabled={(data?.total ?? 0) === 0 || batchMutation.isPending}
            onClick={() => batchMutation.mutate()}
          >
            Test all {data?.total ? `(${data.total})` : ""}
          </Button>
        </div>
      </div>
      <FilterBar
        values={filters}
        onChange={setFilters}
        onExport={exportFile}
        onScrape={() => scrapeMutation.mutate()}
      />
      {progress ? <ProgressBar {...progress} /> : null}
      <ProxyTable
        loading={isLoading}
        proxies={proxies}
      />
    </section>
  );
}
