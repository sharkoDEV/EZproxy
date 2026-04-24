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

  useEffect(() => {
    socket.connect();
    socket.on("progress", setProgress);
    return () => {
      socket.off("progress", setProgress);
      socket.disconnect();
    };
  }, [setProgress]);

  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </QueryClientProvider>
  );
}
