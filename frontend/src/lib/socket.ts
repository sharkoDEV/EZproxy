import { io } from "socket.io-client";

export const SOCKET_BASE_URL =
  process.env.NEXT_PUBLIC_SOCKET_URL ?? "http://localhost:8000";

export const socket = io(
  `${SOCKET_BASE_URL}/ws/proxies`,
  {
    autoConnect: false,
    path: "/socket.io",
    transports: ["websocket"],
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 500,
    reconnectionDelayMax: 3000,
  },
);
