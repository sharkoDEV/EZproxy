import type { WorkerClientStats } from "@/lib/store";

type WorkerClientTableProps = {
  clients: WorkerClientStats[];
};

function formatLastSeen(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "n/a";
  }
  return date.toLocaleTimeString();
}

export function WorkerClientTable({ clients }: WorkerClientTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-panel">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-neon">
            Worker clients
          </p>
          <h3 className="text-lg font-black text-white">
            Connected checkers: {clients.filter((client) => client.active).length}
          </h3>
        </div>
        <span className="rounded-full border border-neon px-3 py-1 text-xs font-bold text-neon">
          Live
        </span>
      </div>
      <div className="max-h-64 overflow-auto">
        <table className="w-full table-auto text-left text-sm">
          <thead className="sticky top-0 bg-void text-xs uppercase tracking-[0.25em] text-zinc-500">
            <tr>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">In flight</th>
              <th className="px-4 py-3">Reported</th>
              <th className="px-4 py-3">Valid</th>
              <th className="px-4 py-3">Stored</th>
              <th className="px-4 py-3">Last seen</th>
            </tr>
          </thead>
          <tbody>
            {clients.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-center text-zinc-500" colSpan={7}>
                  No C worker has connected yet.
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <tr
                  className="border-t border-line/70 text-zinc-300"
                  key={client.worker_id}
                >
                  <td className="px-4 py-3 font-semibold text-white">
                    {client.worker_id}
                  </td>
                  <td
                    className={`px-4 py-3 font-bold ${
                      client.active ? "text-neon" : "text-magenta"
                    }`}
                  >
                    {client.active ? "online" : "stale"}
                  </td>
                  <td className="px-4 py-3">{client.in_flight}</td>
                  <td className="px-4 py-3">{client.reported}</td>
                  <td className="px-4 py-3">{client.valid}</td>
                  <td className="px-4 py-3">{client.stored}</td>
                  <td className="px-4 py-3 text-zinc-500">
                    {formatLastSeen(client.last_seen)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
