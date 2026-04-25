# ezProxy Frontend

Next.js 14 + TypeScript interface for ezProxy.

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_SOCKET_URL` from `.env.example` if the backend does not run on localhost.

Use the `Admin` button in the header to unlock manual proxy creation. The frontend stores the admin token in `localStorage` as `ezproxy-token`.
