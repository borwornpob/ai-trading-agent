# Gold Trading Bot — Implementation Plan v2
> Vibe Coding Guide สำหรับ Claude Code  
> Stack: Python (FastAPI) + Next.js + MetaTrader 5 + PostgreSQL + Redis + AI (Claude Haiku)

---

## Project Overview

สร้าง Web Platform สำหรับ Auto-Trading ทองคำ (XAUUSD) ผ่าน MetaTrader 5 โดยมี:
- **Backend**: Python FastAPI — เชื่อม MT5, คำนวณ signal, บริหาร order
- **AI Layer**: Claude Haiku API — news sentiment + weekly strategy optimization
- **Frontend**: Next.js — Dashboard monitor + strategy config
- **Database**: PostgreSQL (trade log) + Redis (real-time cache)
- **Infrastructure**: Windows VPS (MT5 Bridge) + Railway (Backend) + Vercel (Frontend)

### Architecture Overview
```
Vercel → Next.js Frontend
            │
            ▼
Railway → FastAPI Backend
    ├── Strategy Engine (rule-based: EMA, RSI, ATR)
    ├── AI Analysis Module
    │   ├── News Sentiment → Claude Haiku (ทุก 15 นาที)
    │   └── Strategy Optimizer → Claude Haiku (ทุกสัปดาห์)
    ├── PostgreSQL + Redis
    └── ──HTTP──▶ Windows VPS
                  └── MT5 Bridge + MetaTrader 5
```

### ค่าใช้จ่ายโดยประมาณ
| Component | ค่าใช้จ่าย/เดือน |
|---|---|
| Windows VPS (MT5 Bridge) | ~$24 |
| Railway (Backend) | ~$10–20 |
| Vercel (Frontend) | ฟรี |
| Claude Haiku API (AI) | < $0.15 |
| **รวม** | **~$34–45** |

### ข้อควรทราบก่อนเริ่ม
- MT5 Python library รันได้เฉพาะ **Windows** — deploy MT5 Bridge บน Windows VPS
- Backend หลัก (FastAPI) deploy บน **Railway** (Linux) ได้ปกติ
- AI เป็น **enhancement layer** — bot ทำงานได้ถึงแม้ AI call จะ fail
- เริ่มจาก **demo account** เสมอก่อนขึ้น live

---

## Repository Structure

```
gold-trading-bot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── mt5/
│   │   │   ├── connector.py
│   │   │   ├── market_data.py
│   │   │   └── order_executor.py
│   │   ├── strategy/
│   │   │   ├── base.py
│   │   │   ├── ema_crossover.py
│   │   │   └── rsi_filter.py
│   │   ├── ai/                          # ← NEW: AI Analysis Layer
│   │   │   ├── client.py                # Anthropic client wrapper
│   │   │   ├── news_sentiment.py        # sentiment analysis
│   │   │   ├── strategy_optimizer.py    # weekly optimization
│   │   │   └── prompts.py               # prompt templates
│   │   ├── news/                        # ← NEW: News Feed
│   │   │   ├── fetcher.py               # ดึงข่าวจาก RSS / API
│   │   │   └── sources.py               # config news sources
│   │   ├── risk/
│   │   │   ├── manager.py
│   │   │   └── circuit_breaker.py
│   │   ├── bot/
│   │   │   ├── engine.py
│   │   │   └── scheduler.py
│   │   ├── backtest/
│   │   │   └── engine.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── bot.py
│   │   │   │   ├── positions.py
│   │   │   │   ├── history.py
│   │   │   │   ├── strategy.py
│   │   │   │   └── ai_insights.py       # ← NEW: AI insights endpoint
│   │   │   └── websocket.py
│   │   └── db/
│   │       ├── models.py
│   │       └── session.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── mt5_bridge/                          # รันบน Windows VPS
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── strategy/page.tsx
│   │   ├── backtest/page.tsx
│   │   ├── history/page.tsx
│   │   └── insights/page.tsx            # ← NEW: AI Insights page
│   ├── components/
│   │   ├── ui/
│   │   ├── charts/
│   │   ├── bot/
│   │   ├── strategy/
│   │   └── ai/                          # ← NEW
│   │       ├── SentimentBadge.tsx
│   │       ├── NewsCard.tsx
│   │       └── OptimizationReport.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── websocket.ts
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## Phase 1 — Project Setup & MT5 Connection

**เป้าหมาย**: project structure พร้อม, เชื่อม MT5 ได้, อ่าน XAUUSD price ได้

### Prompt 1.1 — Bootstrap project structure

```
สร้าง project structure สำหรับ Gold Trading Bot ตาม layout ด้านล่าง

Repository: gold-trading-bot/
- backend/ → Python FastAPI (deploy บน Railway)
- mt5_bridge/ → Python FastAPI mini (deploy บน Windows VPS)
- frontend/ → Next.js 14 App Router (deploy บน Vercel)
- docker-compose.yml สำหรับ postgres + redis (local dev)

งานที่ต้องทำ:
1. สร้าง backend/ ด้วย Python project structure ตาม layout ที่กำหนด
2. สร้าง requirements.txt ที่มี:
   fastapi, uvicorn, MetaTrader5, pandas, pandas-ta,
   sqlalchemy, alembic, psycopg2-binary, redis, python-dotenv,
   websockets, anthropic, httpx, feedparser, apscheduler
3. สร้าง .env.example ที่มี variables:
   MT5_BRIDGE_URL, DATABASE_URL, REDIS_URL, SECRET_KEY,
   ANTHROPIC_API_KEY, NEWS_API_KEY (optional)
4. สร้าง mt5_bridge/ ที่มี requirements.txt แยก (MetaTrader5, fastapi, uvicorn)
5. สร้าง frontend/ ด้วย Next.js 14 App Router + TypeScript + Tailwind CSS
6. สร้าง docker-compose.yml สำหรับ postgres:15 และ redis:7
7. สร้าง README.md อธิบาย setup steps และ architecture

[วาง repository structure จากด้านบน]
```

### Prompt 1.2 — MT5 Bridge (Windows VPS)

```
สร้าง mt5_bridge/main.py — FastAPI app ที่รันบน Windows VPS เท่านั้น

Requirements:
- เชื่อมต่อ MT5 ด้วย credentials จาก .env ตอน startup
- API Key authentication ด้วย header X-Bridge-Key (ป้องกัน unauthorized access)

Endpoints:
- GET  /health              → MT5 connection status
- GET  /tick/{symbol}       → {"bid": float, "ask": float, "spread": float, "time": str}
- GET  /ohlcv/{symbol}      → query params: timeframe, count → OHLCV as JSON array
- GET  /account             → balance, equity, margin, free_margin
- GET  /positions           → list of open positions
- POST /order               → place order: {symbol, type, lot, sl, tp, comment}
- DELETE /position/{ticket} → close specific position
- DELETE /positions         → close all positions (emergency)

Error handling:
- ถ้า MT5 disconnect ให้ retry reconnect อัตโนมัติ
- return consistent error format: {"success": false, "error": "message"}
- Log ทุก order ด้วย structured logging

สร้าง backend/app/mt5/connector.py:
- HTTP client ที่ call mt5_bridge แทน import MetaTrader5 โดยตรง
- Class MT5BridgeConnector พร้อม methods ครบ: get_tick, get_ohlcv, get_account,
  get_positions, place_order, close_position, close_all_positions
- ใช้ httpx async client
- Timeout 5 วินาทีต่อ request
- Retry 2 ครั้งถ้า timeout
```

### Prompt 1.3 — Market Data & Database

```
สร้าง backend/app/mt5/market_data.py:
- function get_current_tick(symbol) → dict
- function get_ohlcv(symbol, timeframe, count) → pandas DataFrame
  columns: time, open, high, low, close, tick_volume
- function stream_ticks(symbol, callback, interval=1.0)
  loop ที่ call callback ทุก interval วินาที พร้อม latest tick

สร้าง backend/app/db/models.py (SQLAlchemy):
- OHLCVData: id, symbol, timeframe, time, open, high, low, close, volume
- Trade: id, ticket, symbol, type, lot, open_price, close_price,
  sl, tp, open_time, close_time, profit, comment, strategy_name,
  ai_sentiment_score (float, nullable),    ← เก็บ sentiment ตอนเปิด trade
  ai_sentiment_label (str, nullable)        ← "bullish"/"bearish"/"neutral"
- NewsSentiment: id, headline, source, published_at, sentiment_label,
  sentiment_score, confidence, raw_response, created_at
- AIOptimizationLog: id, period_start, period_end, current_params,
  suggested_params, rationale, applied (bool), created_at
- BotEvent: id, event_type, message, created_at

สร้าง backend/app/db/session.py:
- SQLAlchemy async engine + SessionLocal
- get_db() dependency

สร้าง Alembic migration สำหรับ models ทั้งหมด
```

---

## Phase 2 — Strategy Engine & Backtester

**เป้าหมาย**: คำนวณ signal ได้, backtest บน historical data ได้

### Prompt 2.1 — Strategy Base & Indicators

```
สร้าง Strategy system

สร้าง backend/app/strategy/base.py:
- Abstract class BaseStrategy
  - abstract method: calculate(df: pd.DataFrame) → pd.DataFrame
    return df ที่มี column 'signal': 1=BUY, -1=SELL, 0=HOLD
  - abstract method: get_params() → dict
  - property: name (str)
  - property: min_bars_required (int)

สร้าง backend/app/strategy/ema_crossover.py:
- Class EMACrossoverStrategy(BaseStrategy)
- params: fast_period=20, slow_period=50
- คำนวณ EMA ด้วย pandas-ta
- BUY: fast EMA crosses above slow EMA
- SELL: fast EMA crosses below slow EMA
- เพิ่ม columns: ema_fast, ema_slow, signal, atr (ATR-14 สำหรับ SL/TP)

สร้าง backend/app/strategy/rsi_filter.py:
- Class RSIFilterStrategy(BaseStrategy)
- params: ema_fast=20, ema_slow=50, rsi_period=14,
  rsi_overbought=70, rsi_oversold=30
- BUY: EMA cross up AND RSI < rsi_overbought
- SELL: EMA cross down AND RSI > rsi_oversold

สร้าง backend/app/strategy/__init__.py:
- STRATEGIES dict
- function get_strategy(name, params) → BaseStrategy instance
```

### Prompt 2.2 — Risk Manager

```
สร้าง backend/app/risk/manager.py

Class RiskManager:
- constructor: max_risk_per_trade, max_daily_loss, max_concurrent_trades, max_lot=1.0

- method calculate_lot_size(balance, sl_pips, pip_value=1.0) → float
  lot = (balance × risk%) ÷ (sl_pips × pip_value × 100)
  round 2 decimal, cap ที่ max_lot

- method calculate_sl_tp(entry_price, signal, atr, sl_mult=1.5, tp_mult=2.0) → (sl, tp)
  ATR-based: BUY → sl = entry - (atr × sl_mult), tp = entry + (atr × tp_mult)

- method can_open_trade(current_positions, daily_pnl, ai_sentiment=None) → (bool, str)
  return False ถ้า:
  - positions >= max_concurrent_trades
  - daily_pnl <= -(balance × max_daily_loss)
  - ai_sentiment == "bearish" และ signal == BUY (ถ้า ai_sentiment_filter เปิดอยู่)
  - ai_sentiment == "bullish" และ signal == SELL

สร้าง backend/app/risk/circuit_breaker.py:
- ติดตาม daily P&L จาก Redis (reset เที่ยงคืน UTC)
- method record_trade_result(profit)
- method get_daily_pnl() → float
- method is_triggered() → bool
```

### Prompt 2.3 — Backtester

```
สร้าง backend/app/backtest/engine.py

Class BacktestEngine:
- constructor: symbol, timeframe, strategy, risk_manager

- method run(start_date, end_date, use_ai_filter=False) → BacktestResult
  ถ้า use_ai_filter=True ให้ simulate ด้วย mock sentiment data
  (สุ่ม sentiment จาก distribution ที่ configurable)

BacktestResult dataclass:
- trades: List[dict]
- total_trades, win_rate, total_profit
- max_drawdown, sharpe_ratio, profit_factor
- equity_curve: List[float]
- ai_filtered_trades: int  ← จำนวน trade ที่ถูก AI filter ออก (ถ้า use_ai_filter=True)

Logic:
1. ดึง OHLCV จาก DB
2. คำนวณ signals ด้วย strategy.calculate(df)
3. Simulate bar-by-bar (ไม่ look-ahead)
4. Simulate SL/TP hit ด้วย High/Low
5. คำนวณ metrics

สร้าง backend/app/api/routes/backtest.py:
- POST /api/backtest/run
- GET  /api/backtest/history
```

---

## Phase 3 — AI Analysis Layer

**เป้าหมาย**: news sentiment analysis + strategy optimization ด้วย Claude Haiku

### Prompt 3.1 — Anthropic Client & Prompts

```
สร้าง backend/app/ai/client.py

Class AIClient:
- ใช้ anthropic Python SDK (pip install anthropic)
- MODEL = "claude-haiku-4-5-20251001"  (ถูกที่สุด เร็วที่สุด)
- method complete(system_prompt, user_prompt, max_tokens=256) → str
  - ใช้ anthropic.Anthropic().messages.create()
  - Timeout 10 วินาที
  - ถ้า fail ให้ return None (ไม่ raise exception — AI เป็น optional layer)
  - Log token usage ทุก call เพื่อ track cost
- method complete_json(system_prompt, user_prompt, max_tokens=256) → dict | None
  - เรียก complete() แล้ว parse JSON
  - ถ้า parse fail ให้ return None

สร้าง backend/app/ai/prompts.py:

SENTIMENT_SYSTEM_PROMPT = """
You are a gold market analyst. Analyze news headlines and return ONLY a JSON object.
No explanation, no markdown, just raw JSON.

Response format:
{
  "sentiment": "bullish" | "bearish" | "neutral",
  "score": float between -1.0 (very bearish) and 1.0 (very bullish),
  "confidence": float between 0.0 and 1.0,
  "key_factors": ["factor1", "factor2"]
}

Focus on: Fed policy, USD strength, inflation data, geopolitical risk, ETF flows.
Gold is inverse to USD. High inflation = bullish gold. Rate hikes = bearish gold.
"""

OPTIMIZATION_SYSTEM_PROMPT = """
You are a quantitative trading analyst specializing in gold (XAUUSD) algorithmic strategies.
Analyze performance data and return ONLY a JSON object with parameter recommendations.
No explanation, no markdown, just raw JSON.

Response format:
{
  "assessment": "string (2-3 sentences)",
  "suggested_params": {
    "fast_period": int,
    "slow_period": int,
    "rsi_period": int,
    "rsi_overbought": int,
    "rsi_oversold": int,
    "sl_multiplier": float,
    "tp_multiplier": float
  },
  "confidence": float,
  "reasoning": "string"
}
"""
```

### Prompt 3.2 — News Fetcher & Sentiment Analyzer

```
สร้าง backend/app/news/sources.py:

NEWS_SOURCES = [
    {
        "name": "ForexFactory Gold",
        "url": "https://www.forexfactory.com/calendar",
        "type": "calendar"   # high-impact events
    },
    {
        "name": "Kitco News RSS",
        "url": "https://www.kitco.com/rss/news.xml",
        "type": "rss"
    },
    {
        "name": "Reuters Gold RSS",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "type": "rss",
        "filter_keywords": ["gold", "XAU", "bullion", "Fed", "inflation", "dollar"]
    }
]

สร้าง backend/app/news/fetcher.py:

Class NewsFetcher:
- method fetch_rss(url, filter_keywords=None) → List[dict]
  ใช้ feedparser library
  return: [{"title": str, "summary": str, "published": datetime, "source": str}]
- method fetch_all_sources() → List[dict]
  fetch ทุก source ใน NEWS_SOURCES แบบ concurrent (asyncio.gather)
  filter เฉพาะข่าวที่ published ภายใน 2 ชั่วโมงที่ผ่านมา
  deduplicate ด้วย title similarity
  return top 5 ข่าวล่าสุด

สร้าง backend/app/ai/news_sentiment.py:

Class NewsSentimentAnalyzer:
- constructor รับ: ai_client: AIClient, db_session, redis_client

- method analyze(news_items: List[dict]) → SentimentResult
  1. สร้าง user_prompt จาก headlines: "Headlines:\n1. {title}\n2. {title}..."
  2. call ai_client.complete_json(SENTIMENT_SYSTEM_PROMPT, user_prompt)
  3. ถ้า AI fail → return SentimentResult(label="neutral", score=0.0, confidence=0.0)
  4. บันทึกผลลง DB (NewsSentiment table)
  5. cache ผลลง Redis key "sentiment:latest" TTL 15 นาที
  6. return SentimentResult

- method get_latest_sentiment() → SentimentResult
  อ่านจาก Redis ก่อน ถ้าไม่มีค่อย call analyze()

SentimentResult dataclass:
- label: str  ("bullish" / "bearish" / "neutral")
- score: float  (-1.0 ถึง 1.0)
- confidence: float
- key_factors: List[str]
- source_count: int
- analyzed_at: datetime

สร้าง backend/app/api/routes/ai_insights.py:
- GET /api/ai/sentiment → latest sentiment + news headlines
- GET /api/ai/sentiment/history?days=7 → sentiment history
```

### Prompt 3.3 — Strategy Optimizer

```
สร้าง backend/app/ai/strategy_optimizer.py

Class StrategyOptimizer:
- constructor รับ: ai_client, db_session

- method build_performance_summary(days=7) → str
  query trade history จาก DB ย้อนหลัง N วัน
  สร้าง summary string:
  """
  Period: {start} to {end}
  Total trades: {n}
  Win rate: {pct}%
  Average profit: {avg_profit} pips
  Average loss: {avg_loss} pips
  Max drawdown: {max_dd}%
  Profit factor: {pf}
  Current params: fast_ema={x}, slow_ema={y}, rsi={z}
  Recent losing trades pattern: {pattern description}
  """

- method optimize(current_params: dict) → OptimizationResult | None
  1. build_performance_summary()
  2. สร้าง user_prompt: "Current performance:\n{summary}\nCurrent params: {params}"
  3. call ai_client.complete_json(OPTIMIZATION_SYSTEM_PROMPT, user_prompt, max_tokens=512)
  4. ถ้า AI fail → return None
  5. validate suggested_params (range check: fast_period 5-50, slow_period 20-200 ฯลฯ)
  6. บันทึกลง AIOptimizationLog table (applied=False)
  7. return OptimizationResult

OptimizationResult dataclass:
- assessment: str
- current_params: dict
- suggested_params: dict
- confidence: float
- reasoning: str
- log_id: int  (สำหรับ mark applied ภายหลัง)

สร้าง backend/app/api/routes/ai_insights.py (เพิ่ม):
- GET  /api/ai/optimization/latest → latest optimization report
- POST /api/ai/optimization/run   → trigger manual optimization
- POST /api/ai/optimization/{id}/apply → apply suggested params (ต้อง stop bot ก่อน)
```

---

## Phase 4 — Bot Engine & Order Execution

**เป้าหมาย**: bot loop ทำงานได้จริง, integrat AI sentiment เข้า decision flow

### Prompt 4.1 — Order Executor

```
สร้าง backend/app/mt5/order_executor.py

Class OrderExecutor:
- method place_order(symbol, order_type, lot, sl, tp, comment, magic=234000) → dict
- method close_position(ticket) → dict
- method close_all_positions(symbol=None) → List[dict]
- method get_open_positions(symbol=None) → List[dict]
- method modify_position(ticket, sl=None, tp=None) → dict

ทุก method call ผ่าน MT5BridgeConnector (HTTP)
Log ทุก order attempt และ result ด้วย structured logging (JSON)

Error handling:
- Timeout → retry 1 ครั้ง
- Error อื่น → log + raise
```

### Prompt 4.2 — Bot Engine พร้อม AI Integration

```
สร้าง backend/app/bot/engine.py

Class BotEngine:
- constructor รับ: strategy, risk_manager, connector, executor,
  sentiment_analyzer, db_session, redis_client
- State: STOPPED | RUNNING | PAUSED | ERROR
- method start(), stop(), emergency_stop()
- method get_status() → dict

Main loop (ทุก candle close ตาม timeframe):
1. ตรวจ circuit breaker → stop ถ้า triggered
2. ดึง OHLCV ล่าสุด
3. คำนวณ signal ด้วย strategy.calculate(df)
4. ถ้ามี signal (1 หรือ -1):
   a. ดึง latest sentiment จาก sentiment_analyzer.get_latest_sentiment()
   b. call risk_manager.can_open_trade(positions, daily_pnl, ai_sentiment=sentiment)
      → ถ้า sentiment.confidence > 0.7 ให้ใช้ sentiment filter
      → ถ้า confidence < 0.7 ให้ ignore sentiment (ไม่แน่ใจ → ปล่อยผ่าน)
   c. คำนวณ lot + SL/TP
   d. place_order()
   e. บันทึก Trade พร้อม ai_sentiment_score และ ai_sentiment_label
   f. push event ผ่าน Redis
5. sync open positions
6. อัพเดต daily_pnl

สร้าง backend/app/bot/scheduler.py (APScheduler):
- Job: bot_tick         → ทุก 1 วินาที (update Redis price cache)
- Job: bot_candle       → ทุก 15 นาที (run strategy + signal)
- Job: fetch_sentiment  → ทุก 15 นาที (fetch news + analyze)
- Job: sync_positions   → ทุก 30 วินาที
- Job: weekly_optimize  → ทุกวันจันทร์ 06:00 UTC (run AI optimization)
- Job: daily_reset      → เที่ยงคืน UTC (reset circuit breaker)
```

### Prompt 4.3 — FastAPI Application

```
สร้าง backend/app/main.py และ routes ทั้งหมด

main.py:
- FastAPI app พร้อม CORS
- startup: init MT5 connector, start scheduler, run initial sentiment fetch
- shutdown: stop bot, shutdown MT5
- include routers: bot, positions, history, strategy, ai_insights, backtest

สร้าง backend/app/api/routes/bot.py:
- POST /api/bot/start
- POST /api/bot/stop
- POST /api/bot/emergency-stop
- GET  /api/bot/status  (รวม current sentiment ไว้ด้วย)
- PUT  /api/bot/strategy
- PUT  /api/bot/settings  (toggle: use_ai_filter bool)

สร้าง backend/app/api/websocket.py:
- WebSocket /ws
- Push channels: price_update, position_update, bot_event, sentiment_update
```

---

## Phase 5 — Frontend Dashboard

**เป้าหมาย**: Web UI ครบ + แสดง AI insights

### Prompt 5.1 — Setup & Layout

```
Setup Next.js 14 frontend

Dependencies:
- axios, lightweight-charts, recharts
- shadcn/ui: Button, Card, Badge, Switch, Input, Slider, Table, Tabs
- date-fns, zustand

สร้าง frontend/lib/api.ts:
- functions: getBotStatus, startBot, stopBot, emergencyStop,
  getPositions, getTradeHistory, runBacktest, updateStrategy,
  getLatestSentiment, getSentimentHistory,    ← NEW
  getOptimizationReport, runOptimization, applyOptimization  ← NEW

สร้าง frontend/lib/websocket.ts:
- hook: useWebSocket()
- channels: price_update, position_update, bot_event, sentiment_update
- Auto-reconnect + exponential backoff

สร้าง frontend/app/layout.tsx:
- Sidebar: Dashboard, Strategy, Backtest, History, AI Insights  ← NEW
- Header: connection status, account balance, sentiment badge   ← NEW (mini badge)
- Dark theme default
```

### Prompt 5.2 — Dashboard Page

```
สร้าง frontend/app/dashboard/page.tsx

Row 1 — Stats Cards (5 cards):
- Account Balance (equity + floating P&L)
- Daily P&L (ตัวเลข + % สีตาม positive/negative)
- Open Positions (จำนวน + unrealized profit)
- Bot Status (badge + uptime)
- AI Sentiment ← NEW (badge: 🟢 Bullish / 🔴 Bearish / ⚪ Neutral + score)

Row 2 — Price Chart (65%) + Controls (35%):
Price Chart (TradingView Lightweight Charts):
- Candlestick XAUUSD
- EMA fast + slow overlay
- BUY/SELL markers
- Sentiment annotation: แสดง sentiment label เล็ก ๆ บน chart ทุก 15 นาที ← NEW
- Timeframe selector

Controls panel:
- Start/Stop button
- Emergency Stop (สีแดง, confirm dialog)
- AI Filter toggle: เปิด/ปิด sentiment filter  ← NEW
- Current strategy + params

Row 3 — News Feed (ใหม่) + Open Positions:
News Feed (ครึ่งซ้าย) ← NEW:
- แสดง 3-5 ข่าวล่าสุด
- แต่ละข่าวมี: headline, source, time, sentiment badge
- "Last analyzed: X minutes ago"

Open Positions (ครึ่งขวา):
- columns: Type, Lots, Entry, Current, SL, TP, P&L, Close
- สี BUY=เขียว SELL=แดง
- Real-time P&L update
```

### Prompt 5.3 — AI Insights Page

```
สร้าง frontend/app/insights/page.tsx

Section 1 — Current Sentiment:
- Gauge chart แสดง sentiment score (-1 ถึง 1)
  ใช้ Recharts RadialBarChart หรือ custom SVG
- Label: BEARISH / NEUTRAL / BULLISH พร้อม confidence %
- Key factors list (จาก AI response)
- Last updated time

Section 2 — Sentiment History Chart:
- Line chart (Recharts) แสดง sentiment score ย้อนหลัง 7 วัน
- X-axis: time, Y-axis: score (-1 ถึง 1)
- แถบสี background: เขียวเมื่อ > 0.3, แดงเมื่อ < -0.3
- Overlay กับ XAUUSD price (dual Y-axis)

Section 3 — Strategy Optimization Report:
- Card แสดง latest optimization:
  Assessment text (จาก AI)
  Comparison table: Current params vs Suggested params
  Confidence meter
  Reasoning text
- "Apply Suggestions" button (disabled ถ้า bot running)
  → confirm dialog → call POST /api/ai/optimization/{id}/apply
- "Run Optimization Now" button

Section 4 — AI Performance Attribution:
- ตารางแสดงว่า AI filter ช่วยหรือเสียหายเท่าไหร่
  columns: Month, Trades Filtered, Avoided Loss, Win Rate w/ AI, Win Rate w/o AI
```

### Prompt 5.4 — Strategy & History Pages

```
สร้าง frontend/app/strategy/page.tsx:

Section 1 — Strategy Selector:
- Dropdown: "EMA Crossover", "RSI Filter"

Section 2 — Parameters Form (dynamic):
EMA Crossover: fast_period, slow_period (slider + input)
RSI Filter: + rsi_period, rsi_overbought, rsi_oversold

Section 3 — Risk Parameters:
- Risk per trade % (slider 0.1–5%, default 1%)
- Max daily loss % (slider 1–10%, default 3%)
- Max concurrent trades (1-10)
- Max lot size

Section 4 — AI Settings ← NEW:
- Toggle: Enable AI Sentiment Filter
- Confidence threshold slider (0.5–0.9, default 0.7)
  "Only apply filter when AI confidence ≥ X%"
- Info text: "When enabled, bot won't open trades that contradict AI sentiment"

Section 5 — Backtest Preview:
- Date range + "Run Quick Backtest" button
- Mini results: Win Rate, Profit Factor, Max DD

สร้าง frontend/app/history/page.tsx:
Trades tab:
- Filter: date range, type, strategy
- Table + columns รวม: AI Sentiment (icon) ← NEW
- Export CSV

Performance tab:
- Monthly P&L chart
- AI Filter Attribution stats ← NEW
```

---

## Phase 6 — Deployment

**เป้าหมาย**: ระบบทำงาน production ได้

### Prompt 6.1 — Windows VPS Setup

```
สร้าง scripts/setup_windows_vps.md:
อธิบาย step-by-step:
1. เช่า Windows VPS (แนะนำ Vultr — Windows Server 2022, 2vCPU/4GB ~$24/month)
2. RDP เข้าไปที่ VPS
3. ติดตั้ง Python 3.11
4. ติดตั้ง MetaTrader 5 + login broker (demo account ก่อน)
5. Clone repo → cd mt5_bridge
6. pip install -r requirements.txt
7. สร้าง .env (MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, BRIDGE_API_KEY)
8. รัน: uvicorn main:app --host 0.0.0.0 --port 8001
9. เปิด Windows Firewall port 8001
10. ทดสอบ: curl http://VPS_IP:8001/health

สร้าง mt5_bridge/watchdog.py:
- Monitor main.py process
- Auto-restart ถ้า crash (max 3 ครั้ง/ชั่วโมง)
- ส่ง Telegram alert เมื่อ restart
```

### Prompt 6.2 — Railway & Vercel Deploy

```
สร้าง config files สำหรับ Railway และ Vercel

สร้าง backend/railway.toml:
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

สร้าง backend/Procfile (backup):
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT

สร้าง frontend/vercel.json:
{
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url",
    "NEXT_PUBLIC_WS_URL": "@ws_url"
  }
}

Railway environment variables ที่ต้อง set:
- DATABASE_URL (Railway PostgreSQL plugin)
- REDIS_URL (Railway Redis plugin)
- MT5_BRIDGE_URL=http://YOUR_VPS_IP:8001
- MT5_BRIDGE_API_KEY=your_secret_key
- ANTHROPIC_API_KEY=sk-ant-...
- SECRET_KEY=random_32_chars
- TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

### Prompt 6.3 — Monitoring & Alerts

```
สร้าง backend/app/notifications/telegram.py:
- Class TelegramNotifier
- method send_trade_alert(type, symbol, price, sl, tp, lot, sentiment_label)
  format: "🟢 BUY XAUUSD @ 2345.50 | Lot: 0.05 | SL: 2330 | TP: 2370 | Sentiment: Bullish"
- method send_sentiment_alert(label, score, key_factors)
  ส่งเมื่อ sentiment เปลี่ยนจาก neutral → bullish/bearish หรือกลับกัน
- method send_optimization_report(result: OptimizationResult)
  ส่งทุกสัปดาห์หลัง weekly optimization
- method send_daily_report(stats)
- method send_error_alert(error)

สร้าง backend/app/health.py:
- GET /health → {status, mt5_connected, db_connected, redis_connected,
                  ai_available, bot_state, last_sentiment_at}

เพิ่ม structured logging ทั่ว application:
- ใช้ loguru
- JSON format สำหรับ production
- Log AI token usage ทุก call (เพื่อ track cost)
- Log rotation: ทุกวัน, เก็บ 30 วัน
```

---

## AI Decision Flow สรุป

```
ทุก 15 นาที:
┌─────────────────────────────────────────────────────┐
│  NewsFetcher.fetch_all_sources()                    │
│  → ดึงข่าวล่าสุด 2 ชั่วโมง (5 headlines)           │
│                    ↓                                │
│  NewsSentimentAnalyzer.analyze(news)               │
│  → Claude Haiku: ~500 input + ~100 output tokens   │
│  → cost: ~$0.00005 ต่อ call                        │
│  → cache ผลใน Redis TTL 15 นาที                    │
└─────────────────────────────────────────────────────┘

เมื่อมี Trade Signal:
┌─────────────────────────────────────────────────────┐
│  sentiment = get_latest_sentiment()  (จาก Redis)   │
│                                                     │
│  ถ้า confidence >= 0.7:                             │
│    BUY signal + sentiment bearish → SKIP            │
│    SELL signal + sentiment bullish → SKIP           │
│    signal ตรงกับ sentiment → PROCEED               │
│                                                     │
│  ถ้า confidence < 0.7:                              │
│    PROCEED (ไม่ confident พอ ให้ rule-based ตัดสิน) │
└─────────────────────────────────────────────────────┘

ทุกสัปดาห์ (จันทร์ 06:00 UTC):
┌─────────────────────────────────────────────────────┐
│  StrategyOptimizer.optimize(current_params)        │
│  → สรุป performance 7 วัน                          │
│  → Claude Haiku: ~2000 input + ~500 output tokens  │
│  → cost: ~$0.0004 ต่อ call                         │
│  → บันทึกผลลง DB + ส่ง Telegram                    │
│  → รอให้ user approve ก่อน apply                   │
└─────────────────────────────────────────────────────┘
```

---

## Checklist ก่อน Go Live

### ✅ Technical
- [ ] Backtest 1+ ปี: Win Rate > 45%, Profit Factor > 1.3
- [ ] Walk-forward test ผ่าน 4+ รอบ
- [ ] Demo trade 2–4 สัปดาห์ ผลใกล้เคียง backtest
- [ ] Emergency stop ทำงานภายใน 3 วินาที
- [ ] Circuit breaker หยุดได้เมื่อ daily loss ถึง limit
- [ ] AI sentiment fail gracefully (ไม่ crash bot)
- [ ] Telegram alerts ครบทุก event
- [ ] Watchdog restart MT5 bridge ได้

### ✅ AI Layer
- [ ] Sentiment cache hit rate > 90% (ไม่ call API ซ้ำเกินไป)
- [ ] Log token usage ทุก call — monthly cost < $1
- [ ] Confidence threshold tuned (ไม่ filter trade เยอะเกินไป)
- [ ] Backtest with AI filter vs without — AI filter ควรช่วย not hurt

### ✅ Risk
- [ ] Max risk per trade ≤ 1%
- [ ] Max daily loss ≤ 3%
- [ ] ทุก trade มี SL เสมอ
- [ ] ทดสอบ edge case: spread กว้าง, news spike

---

## Environment Variables Reference

```bash
# backend/.env

# MT5 Bridge (Windows VPS)
MT5_BRIDGE_URL=http://YOUR_VPS_IP:8001
MT5_BRIDGE_API_KEY=your_secret_bridge_key

# Database (Railway plugins)
DATABASE_URL=postgresql://user:pass@host:5432/goldbot
REDIS_URL=redis://host:6379/0

# AI
ANTHROPIC_API_KEY=sk-ant-api03-...

# Bot Config
SYMBOL=XAUUSD
TIMEFRAME=M15
MAX_RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.03
MAX_CONCURRENT_TRADES=3
MAX_LOT=1.0
USE_AI_FILTER=true
AI_CONFIDENCE_THRESHOLD=0.7

# Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# API
SECRET_KEY=generate_random_32_char_string
CORS_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app

# mt5_bridge/.env (Windows VPS)
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo
BRIDGE_API_KEY=your_secret_bridge_key  # ตรงกับ MT5_BRIDGE_API_KEY ด้านบน
```

---

## Tips สำหรับ Vibe Coding กับ Claude Code

1. **ทำทีละ Prompt** — รอให้แต่ละไฟล์เสร็จก่อน proceed
2. **ทดสอบ AI module แยกก่อน** — test news_sentiment.py standalone ก่อน integrate กับ bot
3. **AI เป็น optional เสมอ** — ทุก AI call ต้องมี fallback ถ้า fail
4. **Track cost ตั้งแต่แรก** — log token usage ทุก call เพื่อไม่ให้เกินงบ
5. **Demo ก่อน live เสมอ** — อย่า skip validation phase
