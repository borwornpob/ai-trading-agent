# Gold Trading Bot

Auto-Trading Platform สำหรับ XAUUSD (ทองคำ) ผ่าน MetaTrader 5

## Architecture

```
Vercel → Next.js Frontend
            │
            ▼
Railway → FastAPI Backend
    ├── Strategy Engine (EMA, RSI, ATR)
    ├── AI Analysis (Claude Haiku)
    ├── PostgreSQL + Redis
    └── ──HTTP──▶ Windows VPS
                  └── MT5 Bridge + MetaTrader 5
```

## Stack

- **Backend**: Python FastAPI
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **AI**: Claude Haiku (news sentiment + strategy optimization)
- **Database**: PostgreSQL + Redis
- **Trading**: MetaTrader 5 via HTTP Bridge

## Local Development Setup

### 1. Start databases
```bash
docker-compose up -d
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # แก้ไขค่าตามต้องการ
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. MT5 Bridge (Windows VPS only)
```bash
cd mt5_bridge
pip install -r requirements.txt
cp .env.example .env      # ใส่ MT5 credentials
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 4. Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Environment Variables

See `backend/.env.example` and `mt5_bridge/.env.example`
