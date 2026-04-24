type CardStatProps = {
  label: string;
  value: string | number;
  hint: string;
};

export function CardStat({ label, value, hint }: CardStatProps) {
  return (
    <article className="group overflow-hidden rounded-lg border border-line bg-panel p-4 shadow-glow transition duration-200 hover:-translate-y-1 hover:border-neon">
      <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">
        {label}
      </p>
      <div className="mt-3 flex items-end justify-between">
        <strong className="text-3xl font-black text-white">{value}</strong>
        <span className="h-2 w-2 rounded-full bg-neon shadow-glow transition group-hover:bg-magenta" />
      </div>
      <p className="mt-3 text-sm text-zinc-400">{hint}</p>
    </article>
  );
}
