import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/Button";
import { Modal } from "@/components/Modal";
import { createProxyBulk } from "@/lib/api";
import { useAppStore } from "@/lib/store";

const schema = z.object({
  proxies: z.string().min(3, "Paste at least one proxy"),
  type: z.enum(["http", "https", "socks4", "socks5"]),
  country: z.string().optional(),
  anonymity: z.string().optional(),
  test_now: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

type AddProxyModalProps = {
  open: boolean;
  onClose: () => void;
};

export function AddProxyModal({ onClose, open }: AddProxyModalProps) {
  const queryClient = useQueryClient();
  const showToast = useAppStore((state) => state.showToast);
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      proxies: "",
      type: "http",
      country: "",
      anonymity: "",
      test_now: false,
    },
  });

  async function onSubmit(values: FormValues) {
    try {
      const result = await createProxyBulk({
        ...values,
        country: values.country || undefined,
        anonymity: values.anonymity || undefined,
      });
      await queryClient.invalidateQueries({ queryKey: ["proxies"] });
      showToast(
        `${result.added} added, ${result.updated} updated, ${result.skipped} skipped`,
      );
      reset();
      onClose();
    } catch {
      showToast("Admin login required or proxy invalid", "error");
    }
  }

  return (
    <Modal open={open} title="Add manual proxy" onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <label className="block text-sm font-semibold text-zinc-300">
          Proxy list
          <textarea
            className="mt-2 min-h-48 w-full resize-none rounded-md border border-line bg-void px-3 py-2 font-mono text-sm text-ink focus:border-neon"
            placeholder={`1.2.3.4:8080\nhttp://5.6.7.8:3128\nsocks5://9.10.11.12:1080`}
            {...register("proxies")}
          />
        </label>
        <p className="text-xs text-zinc-500">
          One proxy per line. Commas and semicolons work too. URLs can override
          the default type.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="block text-sm font-semibold text-zinc-300">
            Default type
            <select
              className="mt-2 w-full rounded-md border border-line bg-void px-3 py-2 text-ink focus:border-neon"
              {...register("type")}
            >
              <option value="http">HTTP</option>
              <option value="https">HTTPS</option>
              <option value="socks4">SOCKS4</option>
              <option value="socks5">SOCKS5</option>
            </select>
          </label>
          <label className="block text-sm font-semibold text-zinc-300">
            Country
            <input
              className="mt-2 w-full rounded-md border border-line bg-void px-3 py-2 text-ink focus:border-neon"
              placeholder="FR"
              {...register("country")}
            />
          </label>
        </div>
        <label className="block text-sm font-semibold text-zinc-300">
          Anonymity
          <input
            className="mt-2 w-full rounded-md border border-line bg-void px-3 py-2 text-ink focus:border-neon"
            placeholder="elite, anonymous..."
            {...register("anonymity")}
          />
        </label>
        <label className="flex items-center gap-3 text-sm font-semibold text-zinc-300">
          <input
            className="h-4 w-4 accent-neon"
            type="checkbox"
            {...register("test_now")}
          />
          Test every pasted proxy now. Leave off for big lists.
        </label>
        {Object.values(errors).length ? (
          <p className="text-sm text-magenta">Check the proxy fields.</p>
        ) : null}
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? "Saving..." : "Add proxy"}
        </Button>
      </form>
    </Modal>
  );
}
