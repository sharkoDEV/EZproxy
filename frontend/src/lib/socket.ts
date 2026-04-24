import { io } from "socket.io-client";

export const socket = io(
  process.env.NEXT_PUBLIC_SOCKET_URL ?? "http://localhost:8000",
  {
    autoConnect: false,
    path: "/socket.io",
    transports: ["websocket"],
  },
);
