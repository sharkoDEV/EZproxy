import { useRouter } from "next/router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Button } from "@/components/Button";
import { api, fetchProxy } from "@/lib/api";
import { useAppStore } from "@/lib/store";

type EditForm = {
  type: string;
  country?: string;
  anonymity?: string;
  status?: string;
};

export default function ProxyDetail() {
  const router = useRouter();
  const id = router.query.id as string | undefined;
  const queryClient = useQueryClient();
  const showToast = useAppStore((state) => state.showToast);
  const form = useForm<EditForm>();

  const { data, isLoading } = useQuery({
    queryKey: ["proxy", id],
    queryFn: async () => {
      const proxy = await fetchProxy(id as string);
      form.reset({
        type: proxy.type,
        country: proxy.country ?? "",
        anonymity: proxy.anonymity ?? "",
        status: proxy.status,
      });
      return proxy;
    },
    enabled: Boolean(id),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: EditForm) => api.patch(`/proxies/${id}`, payload),
    onSuccess: () => {
      showToast("Proxy updated");
      queryClient.invalidateQueries({ queryKey: ["proxies"] });
      router.push("/proxies");
    },
    onError: () => showToast("Update failed", "error"),
  });

  if (isLoading || !data) {
    return (
      <div className="rounded-lg border border-line bg-panel p-6 text-zinc-400">
        Loading proxy...
      </div>
    );
  }

  return (
    <section className="h-full overflow-auto">
      <div className="mb-6">
        <p className="text-sm uppercase tracking-[0.35em] text-neon">
          Proxy detail
        </p>
        <h2 className="mt-1 text-3xl font-black text-white">
          {data.ip}:{data.port}
        </h2>
      </div>
      <form
        className="max-w-xl space-y-4 rounded-xl border border-line bg-panel p-6 shadow-glow"
        onSubmit={form.handleSubmit((payload) =>
          updateMutation.mutate(payload),
        )}
      >
        {["type", "country", "anonymity", "status"].map((name) => (
          <label
            className="block text-sm font-semibold text-zinc-300"
            key={name}
          >
            {name}
            <input
              className="mt-2 w-full rounded-md border border-line bg-void px-3 py-2 text-ink focus:border-neon"
              {...form.register(name as keyof EditForm)}
            />
          </label>
        ))}
        <div className="flex gap-2">
          <Button disabled={updateMutation.isPending} type="submit">
            Save changes
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.push("/proxies")}
          >
            Back
          </Button>
        </div>
      </form>
    </section>
  );
}
