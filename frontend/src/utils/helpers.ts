import type { ProxyRecord } from "@/lib/api";

export function formatLatency(value?: number | null) {
  return typeof value === "number" ? `${Math.round(value)} ms` : "n/a";
}

export function statusTone(status: ProxyRecord["status"]) {
  if (status === "alive") {
    return "text-neon";
  }
  if (status === "dead") {
    return "text-magenta";
  }
  return "text-zinc-400";
}
