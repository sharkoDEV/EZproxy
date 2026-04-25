# ezProxy

ezProxy is a free proxy management SaaS-style app. It scrapes public proxy lists, stores proxies with SQLModel, tests them through `http://httpbin.org/ip`, re-checks stale entries on a configurable interval, exposes a REST API and streams status updates through Socket.IO. The public dashboard stays read/export focused; manual proxy creation is protected by one local admin password.

## Stack

- Backend: FastAPI, SQLModel, aiohttp, python-socketio, PostgreSQL-compatible `DATABASE_URL`
- Frontend: Next.js 14, TypeScript 5, Tailwind CSS 3, React Query v5, Axios, Zustand, Heroicons, React Hook Form, Zod
- CI: GitHub Actions for backend lint/tests and frontend lint/typecheck/build

## Quick Start

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
$env:ADMIN_PASSWORD="change-me"
uvicorn backend.app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the UI at `http://localhost:3000` and Swagger at `http://localhost:8000/docs`.

Click `Admin` in the header, enter `ADMIN_PASSWORD`, then use `Add proxy` on the Proxies page. Manually added proxies are pinned with `is_manual=true`, kept in the database after backend restarts, and are not auto-deleted when a check marks them dead.

## Configuration

Backend behavior is centralized in `config.json`:

- `sources`: public proxy sources and parser names
- `test.url`: URL used to validate proxies
- `test.timeout`: per-proxy timeout in seconds
- `test.max_workers`: max concurrent proxy tests
- `test.recheck_interval_minutes`: automatic re-check interval
- `filters`: default type, country, anonymity and latency filters

Use `.env.example` as a starting point. If `DATABASE_URL` is not set, ezProxy uses `sqlite:///./ezproxy.db` so local development can start without PostgreSQL. For production-like use, set:

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ezproxy
ADMIN_PASSWORD=change-me
ADMIN_TOKEN_SECRET=change-this-local-secret
```

Frontend environment variables live in `frontend/.env.example`.

## API

- `GET /api/v1/health`
- `POST /api/v1/admin/login`
- `GET /api/v1/admin/me`
- `GET /api/v1/proxies`
- `POST /api/v1/proxies` with admin bearer token
- `GET /api/v1/proxies/stats`
- `GET /api/v1/proxies/export?format=txt|csv|json`

Socket.IO uses namespace `/ws/proxies` and emits `proxy_status` plus `progress`.

## UI Notes

The interface is intentionally black, fixed and neon-accented. Header, sidebar and footer stay pinned; content panels scroll internally. Keyboard users get visible neon focus rings, and the theme toggle persists in `localStorage`.

## Useful Commands

```bash
ruff check backend
pytest backend
npm run lint --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
```

No Docker is required.
