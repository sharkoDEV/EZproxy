import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { loginAdmin } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { Button } from "./Button";
import { Modal } from "./Modal";

const schema = z.object({
  password: z.string().min(1, "Password required"),
});

type FormValues = z.infer<typeof schema>;

type AdminLoginModalProps = {
  open: boolean;
  onClose: () => void;
};

export function AdminLoginModal({ onClose, open }: AdminLoginModalProps) {
  const setAdminToken = useAppStore((state) => state.setAdminToken);
  const showToast = useAppStore((state) => state.showToast);
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { password: "" },
  });

  async function onSubmit(values: FormValues) {
    try {
      const session = await loginAdmin(values.password);
      setAdminToken(session.token);
      showToast("Admin connected");
      reset();
      onClose();
    } catch {
      showToast("Wrong admin password", "error");
    }
  }

  return (
    <Modal open={open} title="Admin login" onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <label className="block text-sm font-semibold text-zinc-300">
          Password
          <input
            className="mt-2 w-full rounded-md border border-line bg-void px-3 py-2 text-ink focus:border-neon"
            type="password"
            autoComplete="current-password"
            {...register("password")}
          />
        </label>
        {errors.password ? (
          <p className="text-sm text-magenta">{errors.password.message}</p>
        ) : null}
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? "Checking..." : "Connect"}
        </Button>
      </form>
    </Modal>
  );
}
