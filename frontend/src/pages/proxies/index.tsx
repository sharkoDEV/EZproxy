import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/router";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/Button";
import { FilterBar } from "@/components/FilterBar";
import { Modal } from "@/components/Modal";
import { ProgressBar } from "@/components/ProgressBar";
import { ProxyTable } from "@/components/ProxyTable";
import { api, fetchProxies, fetchProxyIds } from "@/lib/api";
import { useAppStore } from "@/lib/store";

const proxySchema = z.object({
  ip: z.string().min(7),
  port: z.coerce.number().int().min(1).max(65535),
  type: z.string().default("http"),
  country: z.string().optional(),
  anonymity: z.string().optional(),
});

type ProxyForm = z.infer<typeof proxySchema>;

export default function ProxiesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const showToast = useAppStore((state) => state.showToast);
  const progress = useAppStore((state) => state.progress);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    type: "",
    country: "",
    anonymity: "",
  });
  const form = useForm<ProxyForm>({
    resolver: zodResolver(proxySchema),
    defaultValues: { type: "http" },
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
  const createMutation = useMutation({
    mutationFn: (payload: ProxyForm) => api.post("/proxies", payload),
    onSuccess: () => {
      showToast("Proxy added");
      setOpen(false);
      form.reset({ type: "http" });
      invalidate();
    },
    onError: () => showToast("Could not add proxy", "error"),
  });
  const scrapeMutation = useMutation({
    mutationFn: () => api.post("/proxies/scrape"),
    onSuccess: () => {
      showToast("Sources scraped");
      invalidate();
    },
    onError: () => showToast("Scrape failed", "error"),
  });
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/proxies/${id}`),
    onSuccess: () => {
      showToast("Proxy deleted");
      invalidate();
    },
  });
  const testMutation = useMutation({
    mutationFn: (id: number) => api.post(`/proxies/${id}/test`),
    onSuccess: () => {
      showToast("Proxy tested");
      invalidate();
    },
    onError: () => showToast("Test failed", "error"),
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
          <Button variant="secondary" onClick={() => setOpen(true)}>
            Add proxy
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
        onDelete={(id) => deleteMutation.mutate(id)}
        onEdit={(id) => router.push(`/proxies/${id}`)}
        onTest={(id) => testMutation.mutate(id)}
      />
      <Modal
        open={open}
        title="Add proxy manually"
        onClose={() => setOpen(false)}
      >
        <form
          className="space-y-3"
          onSubmit={form.handleSubmit((payload) =>
            createMutation.mutate(payload),
          )}
        >
          {["ip", "port", "type", "country", "anonymity"].map((name) => (
            <input
              className="w-full rounded-md border border-line bg-void px-3 py-2 text-ink focus:border-neon"
              key={name}
              placeholder={name}
              {...form.register(name as keyof ProxyForm)}
            />
          ))}
          <Button disabled={createMutation.isPending} type="submit">
            Save proxy
          </Button>
        </form>
      </Modal>
    </section>
  );
}
