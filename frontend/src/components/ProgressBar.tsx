type ProgressBarProps = {
  tested: number;
  total: number;
  valid: number;
};

export function ProgressBar({ tested, total, valid }: ProgressBarProps) {
  const percent = total > 0 ? Math.round((tested / total) * 100) : 0;

  return (
    <div className="rounded-lg border border-line bg-panel p-4">
      <div className="mb-2 flex items-center justify-between text-sm text-zinc-300">
        <span>Batch testing</span>
        <span>
          {tested}/{total} tested, {valid} valid
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-line">
        <div
          className="h-full bg-neon transition-all duration-200"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
