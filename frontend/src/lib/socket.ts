import { io } from "socket.io-client";

export const socket = io(
  `${process.env.NEXT_PUBLIC_SOCKET_URL ?? "http://localhost:8000"}/ws/proxies`,
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
