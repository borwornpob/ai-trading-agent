# Local Deployment (macOS + Colima)

Quick reference for running the whole stack on your Mac in **shadow mode** (no
real broker calls). MT5 Bridge is skipped because it requires Windows.

## Prerequisites

You said you have Colima. You'll also need these:

```bash
brew install colima docker docker-compose python@3.12 node
colima start                    # start the docker daemon
```

Verify:

```bash
docker info          # must succeed
python3.12 --version # 3.12.x
node --version       # v22 or newer
```

## One-time setup

From the repo root:

```bash
./start-local.sh
```

The script:

1. Checks prerequisites.
2. Starts Postgres (port **5434**) and Redis (port **6380**) via `docker-compose`.
3. Creates `backend/.venv` and installs Python deps.
4. Runs `alembic upgrade head` to create the DB schema.
5. Installs frontend deps with `npm install`.
6. Installs the Claude Code CLI globally (needed by `claude-agent-sdk` for
   the OAuth token flow).

## Running

Two long-running processes — open two terminal tabs.

### Terminal A — backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Terminal B — frontend

```bash
cd frontend
npm run dev
```

UI: http://localhost:3000

## Credentials already configured

| Var | Where | Value |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | `backend/.env` | Your OAuth token (already filled) |
| `POSTGRES_PASSWORD` | `.env` (root) | Auto-generated, matches `backend/.env` |
| `SECRET_KEY`, `VAULT_MASTER_KEY`, `MT5_BRIDGE_API_KEY` | `backend/.env` | Auto-generated |
| `AUTH_PASSWORD_HASH` | `backend/.env` | **Empty** — auth is disabled for local dev |
| `ROLLOUT_MODE` | `backend/.env` | `shadow` — logs trade intent but never calls a broker |

## Stop / reset

```bash
docker-compose down           # stop containers, keep data
docker-compose down -v        # stop AND wipe Postgres/Redis volumes ⚠
```

## Troubleshooting

- **"port 5434 already in use"** — another Postgres is running. Stop it, or
  edit `docker-compose.yml` and change the left side of `"5434:5432"`.
- **`claude-agent-sdk` errors about CLI not found** — install the CLI:
  `npm install -g @anthropic-ai/claude-code@latest`
- **MT5 Bridge / "stale tick" warnings in logs** — expected. We're not running
  the bridge; shadow mode ignores the failure.
- **Frontend fetch errors to `/api/…`** — make sure backend is running on
  port 8000. Next.js expects `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- **Stale `.git` folder** — the existing `.git/` in the repo root is from an
  interrupted earlier clone. You can `rm -rf .git && git init` if you want a
  clean history, or ignore it.

## What about MT5?

MT5 Bridge requires Windows + the MetaTrader 5 terminal installed. You have
three options later on when you want real data:

1. **Spin up a Windows VPS** (cheapest: ~$5/mo on Contabo/Vultr), deploy
   `mt5_bridge/`, and point `MT5_BRIDGE_URL` at it.
2. **Run MT5 in a Windows VM** on your Mac (Parallels / UTM) and point the
   bridge at the VM's IP.
3. **Stay in shadow/paper mode** — plenty of the app works without a real
   broker (backtests, ML training, UI, AI agents).
