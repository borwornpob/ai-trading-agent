#!/usr/bin/env bash
# ---------------------------------------------------------------------
# AI Trading Agent — local bootstrap script (macOS + Colima)
#
# What this does:
#   1. Verifies prerequisites (docker, python3.12, node 22+)
#   2. Starts Postgres + Redis via docker-compose
#   3. Sets up Python venv + installs backend deps
#   4. Runs alembic migrations
#   5. Installs frontend deps
#
# After it finishes, start the two long-running processes in two
# separate terminals:
#
#   Terminal A (backend):
#     cd backend && source .venv/bin/activate && \
#       uvicorn app.main:app --reload --port 8000
#
#   Terminal B (frontend):
#     cd frontend && npm run dev
#
# Then open http://localhost:3000
# ---------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*" >&2; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }

# ─── 1. Prerequisites ────────────────────────────────────────────────
bold "[1/5] Checking prerequisites…"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    red "  ✗ '$1' not found. $2"
    exit 1
  fi
  green "  ✓ $1 found: $(command -v "$1")"
}

need docker         "Install Colima + Docker CLI: 'brew install colima docker docker-compose' then 'colima start'."
need docker-compose "Install docker-compose: 'brew install docker-compose'."
need python3.12     "Install Python 3.12: 'brew install python@3.12'."
need node           "Install Node 22+: 'brew install node@22' (or use nvm)."
need npm            "npm should come with node."

# Docker daemon reachable?
if ! docker info >/dev/null 2>&1; then
  red "  ✗ Docker daemon not reachable. Start Colima: 'colima start'"
  exit 1
fi
green "  ✓ docker daemon reachable"

# Node version check
NODE_MAJOR="$(node --version | sed 's/^v\([0-9]*\).*/\1/')"
if [[ "$NODE_MAJOR" -lt 22 ]]; then
  yellow "  ! Node $NODE_MAJOR detected — frontend needs 22+. Upgrade with: brew upgrade node"
fi

# ─── 2. Docker services (Postgres + Redis) ───────────────────────────
bold "[2/5] Starting Postgres + Redis containers…"
docker-compose up -d
sleep 3
docker ps --filter "name=goldbot-" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Wait for Postgres to be ready
bold "      Waiting for Postgres to accept connections…"
for i in {1..30}; do
  if docker exec goldbot-postgres pg_isready -U goldbot >/dev/null 2>&1; then
    green "      ✓ Postgres ready"
    break
  fi
  sleep 1
  [[ $i -eq 30 ]] && { red "      ✗ Postgres did not become ready in 30s"; exit 1; }
done

# Ensure the database exists (docker-compose auto-creates on first boot)
docker exec goldbot-postgres psql -U goldbot -d goldbot -c 'SELECT 1' >/dev/null 2>&1 || {
  yellow "      ! Creating database 'goldbot'…"
  docker exec goldbot-postgres createdb -U goldbot goldbot || true
}

# ─── 3. Backend: venv + deps ─────────────────────────────────────────
bold "[3/5] Setting up backend venv + installing deps…"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3.12 -m venv .venv
  green "      ✓ created .venv"
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
green "      ✓ backend deps installed"

# Install Claude Code CLI globally (needed by claude-agent-sdk for OAuth login)
if ! command -v claude >/dev/null 2>&1; then
  yellow "      ! Claude Code CLI not found — installing via npm…"
  npm install -g @anthropic-ai/claude-code@latest
fi

# ─── 4. Alembic migrations ───────────────────────────────────────────
bold "[4/5] Running database migrations…"
alembic upgrade head
green "      ✓ migrations applied"

# ─── 5. Frontend: npm install ────────────────────────────────────────
bold "[5/5] Installing frontend deps…"
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
else
  yellow "      ! node_modules/ already exists — skipping (delete to force)"
fi
green "      ✓ frontend deps ready"

# ─── Done ────────────────────────────────────────────────────────────
cat <<EOF

$(green "Setup complete.") Next steps:

  $(bold "Terminal A — backend:")
    cd "$ROOT/backend"
    source .venv/bin/activate
    uvicorn app.main:app --reload --port 8000

  $(bold "Terminal B — frontend:")
    cd "$ROOT/frontend"
    npm run dev

Then open http://localhost:3000

$(bold "Services currently running:")
  • Postgres → localhost:5434 (user: goldbot)
  • Redis    → localhost:6380

$(bold "Stop everything:") docker-compose down
$(bold "Reset DB:")         docker-compose down -v   # ⚠ wipes all data
EOF
