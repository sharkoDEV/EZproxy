import type { AppProps } from "next/app";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout/Layout";
import { socket } from "@/lib/socket";
import { useAppStore } from "@/lib/store";
import "@/styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(() => new QueryClient());
  const setProgress = useAppStore((state) => state.setProgress);
  const setRuntimeStats = useAppStore((state) => state.setRuntimeStats);

  useEffect(() => {
    socket.connect();
    socket.on("progress", setProgress);
    socket.on("stats", setRuntimeStats);
    return () => {
      socket.off("progress", setProgress);
      socket.off("stats", setRuntimeStats);
      socket.disconnect();
    };
  }, [setProgress, setRuntimeStats]);

  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </QueryClientProvider>
  );
}
