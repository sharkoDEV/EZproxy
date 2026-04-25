import type { AppProps } from "next/app";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout/Layout";
import type { ProxyListResponse, ProxyRecord } from "@/lib/api";
import { socket } from "@/lib/socket";
import { useAppStore } from "@/lib/store";
import "@/styles/globals.css";

type ProxyStatusEvent = Pick<ProxyRecord, "status" | "latency_ms"> & {
  id?: number | null;
};

function isProxyListQuery(queryKey: readonly unknown[]) {
  return queryKey[0] === "proxies" && typeof queryKey[1] === "object";
}

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnReconnect: true,
            refetchOnWindowFocus: true,
            staleTime: 0,
          },
        },
      }),
  );
  const setProgress = useAppStore((state) => state.setProgress);
  const setRuntimeStats = useAppStore((state) => state.setRuntimeStats);
  const setSocketConnected = useAppStore((state) => state.setSocketConnected);

  useEffect(() => {
    const refreshEverything = () => {
      setSocketConnected(true);
      queryClient.invalidateQueries({ queryKey: ["proxies"] });
    };

    const markDisconnected = () => {
      setSocketConnected(false);
    };

    const syncProxyStatus = (event: ProxyStatusEvent) => {
      if (!event.id) {
        return;
      }
      queryClient.setQueriesData<ProxyListResponse>(
        { predicate: (query) => isProxyListQuery(query.queryKey) },
        (current) => {
          if (!current) {
            return current;
          }
          let changed = false;
          const items = current.items.map((proxy) => {
            if (proxy.id !== event.id) {
              return proxy;
            }
            changed = true;
            return {
              ...proxy,
              latency_ms: event.latency_ms,
              status: event.status,
            };
          });
          return changed ? { ...current, items } : current;
        },
      );
    };

    const statsHandler = (stats: Parameters<typeof setRuntimeStats>[0]) => {
      setRuntimeStats(stats);
    };

    socket.connect();
    socket.on("connect", refreshEverything);
    socket.on("disconnect", markDisconnected);
    socket.on("connect_error", markDisconnected);
    socket.io.on("reconnect", refreshEverything);
    socket.on("progress", setProgress);
    socket.on("stats", statsHandler);
    socket.on("proxy_status", syncProxyStatus);
    socket.on("proxy_added", refreshEverything);
    return () => {
      socket.off("connect", refreshEverything);
      socket.off("disconnect", markDisconnected);
      socket.off("connect_error", markDisconnected);
      socket.io.off("reconnect", refreshEverything);
      socket.off("progress", setProgress);
      socket.off("stats", statsHandler);
      socket.off("proxy_status", syncProxyStatus);
      socket.off("proxy_added", refreshEverything);
      setSocketConnected(false);
      socket.disconnect();
    };
  }, [queryClient, setProgress, setRuntimeStats, setSocketConnected]);

  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </QueryClientProvider>
  );
}
