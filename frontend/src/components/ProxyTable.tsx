import type { ProxyRecord } from "@/lib/api";
import { formatLatency, statusTone } from "@/utils/helpers";
import { Button } from "./Button";

type ProxyTableProps = {
  proxies: ProxyRecord[];
  loading?: boolean;
  onDelete: (id: number) => void;
  onTest: (id: number) => void;
  onEdit: (id: number) => void;
};

export function ProxyTable({
  proxies,
  loading,
  onDelete,
  onEdit,
  onTest,
}: ProxyTableProps) {
  return (
    <div className="max-h-[calc(100vh-64px-16rem)] overflow-auto rounded-lg border border-line bg-panel">
      <table className="w-full table-auto border-collapse text-left text-sm">
        <thead className="sticky top-0 z-10 bg-[#0d0d0d] text-xs uppercase tracking-[0.2em] text-zinc-500">
          <tr>
            {[
              "IP",
              "Port",
              "Type",
              "Pays",
              "Anonymat",
              "Latence",
              "Statut",
              "Actions",
            ].map((header) => (
              <th className="border-b border-line px-4 py-3" key={header}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td className="px-4 py-8 text-center text-zinc-400" colSpan={8}>
                Loading proxies...
              </td>
            </tr>
          ) : null}
          {!loading && proxies.length === 0 ? (
            <tr>
              <td className="px-4 py-8 text-center text-zinc-400" colSpan={8}>
                No proxies yet. Scrape sources or add one manually.
              </td>
            </tr>
          ) : null}
          {proxies.map((proxy) => (
            <tr
              className="border-b border-line/70 transition hover:bg-white/[0.03]"
              key={proxy.id}
            >
              <td className="px-4 py-3 font-semibold text-white">{proxy.ip}</td>
              <td className="px-4 py-3">{proxy.port}</td>
              <td className="px-4 py-3 uppercase text-neon">{proxy.type}</td>
              <td className="px-4 py-3">{proxy.country ?? "n/a"}</td>
              <td className="px-4 py-3">{proxy.anonymity ?? "n/a"}</td>
              <td className="px-4 py-3">{formatLatency(proxy.latency_ms)}</td>
              <td className={`px-4 py-3 font-bold ${statusTone(proxy.status)}`}>
                {proxy.status}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => onTest(proxy.id)}>
                    Test
                  </Button>
                  <Button variant="ghost" onClick={() => onEdit(proxy.id)}>
                    Edit
                  </Button>
                  <Button variant="ghost" onClick={() => onDelete(proxy.id)}>
                    Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
