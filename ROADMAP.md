# Gold Trading Bot — Development Roadmap

> Last updated: 2026-04-11
> สถานะ: Phase 1–5 ของ plan-v2 เสร็จแล้ว — Roadmap นี้เป็น **next steps** สำหรับการพัฒนาต่อ

---

## Current State Summary

| Area | Status | Notes |
|------|--------|-------|
| Core Trading Engine | ✅ Production-ready | Multi-symbol, MT5 Bridge, paper trading |
| Strategy Engine | ✅ 5 strategies | EMA, RSI, Breakout, Mean Reversion, ML |
| AI Layer | ✅ Functional | Claude Haiku sentiment + weekly optimization |
| ML Pipeline | ✅ Basic | LightGBM 40+ features, manual training |
| Risk Management | ✅ Comprehensive | Circuit breaker, Kelly, position sizing |
| Frontend Dashboard | ✅ Full-featured | Next.js 14, live charts, multi-symbol tabs |
| Test Coverage | ❌ ~0% | Critical gap — empty test directory |
| Documentation | ⚠️ Minimal | README + plan doc only |
| CI/CD | ❌ None | No pipeline, no automated checks |
| Monitoring | ⚠️ Basic | Telegram alerts + loguru, no centralized observability |

---

## Phase 6 — Quality & Stability Foundation

**เป้าหมาย**: สร้าง safety net ก่อนขยาย feature — เพราะนี่คือระบบที่เกี่ยวข้องกับเงินจริง

**Priority**: 🔴 Critical
**Timeline**: 2–3 สัปดาห์

### 6.1 Testing Infrastructure

- [x] Setup pytest + pytest-asyncio + pytest-cov
- [x] สร้าง test fixtures: mock MT5 Bridge, mock AI client, test DB (SQLite in-memory)
- [x] **Unit tests — Strategy layer**
  - ทุก strategy ต้อง test signal generation กับ known datasets
  - Indicator calculations ต้อง match reference values
  - Edge cases: insufficient bars, NaN data, flat market
- [x] **Unit tests — Risk management**
  - Lot sizing calculations (boundary: min lot, max lot, zero balance)
  - Circuit breaker trigger/reset logic
  - Kelly criterion edge cases
- [x] **Integration tests — Bot engine**
  - Full trading loop with mocked MT5
  - AI filter enable/disable paths
  - State transitions: STOPPED → RUNNING → PAUSED → ERROR
- [x] **Integration tests — API routes**
  - Happy path + error responses for all 40+ endpoints
  - WebSocket connection lifecycle
- [x] **Target: ≥70% coverage** on critical paths (strategy, risk, engine) — ✅ ~89% avg

### 6.2 CI/CD Pipeline

- [x] GitHub Actions workflow:
  - Lint (ruff) + type check (mypy) on every PR
  - pytest with coverage gate (fail < 60%)
  - Frontend: ESLint + TypeScript strict check + build
- [x] Pre-commit hooks: ruff format, ruff check
- [ ] Auto-deploy pipeline:
  - Backend → Railway (on merge to main)
  - Frontend → Vercel (auto via Git integration)
  - MT5 Bridge → manual deploy checklist (Windows VPS)

### 6.3 Code Quality Cleanup

- [x] Extract magic numbers → named constants in `constants.py` (40+ constants extracted)
- [x] Refactor large functions in `engine.py` (`process_candle()` 274 → ~40 lines + 6 sub-methods)
- [x] Add input validation (Pydantic `Field`) สำหรับ API endpoints: bot settings, backtest, ML train
- [x] Explicit DB connection pool config (pool_size, max_overflow, pool_timeout, pool_recycle, pool_pre_ping)
- [x] Remove hardcoded credentials (`"changeme"` → `""`) ใน config.py + mt5_bridge/main.py

---

## Phase 7 — Operational Resilience

**เป้าหมาย**: ระบบรันได้ 24/5 อย่างมั่นคง มี observability เพียงพอสำหรับ debug ปัญหา

**Priority**: 🟠 High
**Timeline**: 2–3 สัปดาห์

### 7.1 Monitoring & Observability

- [x] Structured logging → JSON format (`logging_config.py`, daily rotation, error sink, LOG_FORMAT env var)
- [x] Key metrics dashboard (`/api/metrics` endpoint, Redis-backed):
  - Trade execution latency (order placed → confirmation)
  - MT5 Bridge response time + error rate
  - Counters for errors, orders
- [x] Alert rules:
  - MT5 Bridge unreachable > ~90s (3 consecutive health check failures)
  - Daily drawdown approaching limit (80% threshold → Telegram warning)
  - Bot state changed to ERROR (existing Telegram alert)

### 7.2 MT5 Bridge Resilience

- [x] Health check heartbeat: `HealthMonitor` pings Bridge ทุก 30s, auto-pause after 3 consecutive failures
- [x] Reconnection strategy: exponential backoff ใน connector (1s retry), auto-recovery เมื่อ bridge กลับมา
- [x] Order reconciliation: `reconcile_positions()` ทุก 5 min
  - Detect orphaned positions (มีใน MT5 แต่ไม่มีใน DB) → Telegram alert
  - Detect phantom records (มีใน DB แต่ไม่มีใน MT5) → auto-close with 7-day history lookup
- [x] Graceful degradation: Bridge down → pause RUNNING engines, auto-resume on recovery

### 7.3 Data Integrity

- [x] OHLCV data validation: `_validate_ohlcv()` shared method — gaps, duplicates, out-of-order, zero-volume
- [x] Trade audit log: `OrderAudit` table — immutable record of every order attempt + result + latency
- [x] Database backup strategy: `scripts/backup_db.sh` — daily pg_dump, 7-day rotation
- [x] Redis persistence: AOF with `appendfsync everysec` in docker-compose
- [x] Pending trades recovery: `_recover_pending_trades()` job ทุก 5 min — processes Redis fallback

---

## Phase 8 — Advanced Trading Features

**เป้าหมาย**: เพิ่มขีดความสามารถของ trading engine

**Priority**: 🟡 Medium
**Timeline**: 3–4 สัปดาห์

### 8.1 Strategy Enhancements

- [x] **Multi-timeframe analysis (MTF)**: H4/D1 consensus filter (`mtf_filter.py`) + ADX qualifier
- [x] **Session-aware trading**: `SESSION_PROFILES` ใน config — SL/TP override per Asian/London/NY/Overlap/Off
- [x] **Volatility regime detection**: `regime.py` — detect trending_high_vol/trending_low_vol/ranging/normal + parameter adjustments
- [x] **Correlation filter**: expanded matrix, config-based (existing + enhanced)
- [x] **Strategy ensemble**: `ensemble.py` — weighted voting จากหลาย strategies, `get_strategy("ensemble")`

### 8.2 Order Management

- [x] **Trailing stop improvements**: Volatility-adaptive trail (high vol ×1.3, low vol ×0.7) + profit-lock ratchet (>2× ATR → 0.3× step)
- [x] **Break-even automation**: Configurable via `breakeven_atr_mult` setting (default 0.5× ATR)
- [x] **Scaling in/out**: Close-and-reopen partial TP (`_execute_partial_tp`) + momentum scale-in tracking
- [x] **Time-based exit**: Already works, configurable `max_position_duration_hours`
- [x] **Slippage tracking & analysis**: `GET /api/analytics/slippage` — by hour, by strategy, total cost

### 8.3 Backtester v2

- [x] **Walk-forward optimization**: `walk_forward.py` — anchored/sliding windows, overfitting detection
- [x] **Monte Carlo simulation**: `monte_carlo.py` — shuffled sequences, probability of ruin, confidence intervals
- [ ] **Multi-symbol backtesting**: Portfolio-level backtest (planned, not yet implemented)
- [ ] **Realistic simulation**: spread/slippage/swap model (planned, not yet implemented)
- [x] **Comparison mode**: `POST /api/backtest/compare` — side-by-side strategy A vs B

---

## Phase 9 — ML Pipeline Maturity

**เป้าหมาย**: ML model ที่ production-grade — auto-retrain, monitor, และ rollback ได้

**Priority**: 🟡 Medium
**Timeline**: 3–4 สัปดาห์

### 9.1 Automated Training Pipeline

- [x] Scheduled retraining: Monday 04:00 UTC (changed from Sunday 01:00)
- [x] Training data management: 90-day sliding window + 14-day holdout validation split
- [x] Model versioning: metrics per version in MLModelLog, auto-compare with current
- [x] Auto-promotion: only if holdout accuracy improves ≥ 5% over current model
- [x] Rollback mechanism: MLPredictionLog table + auto-rollback when accuracy < 30% (configurable)

### 9.2 Feature Engineering v2

- [x] **Sentiment features**: `sentiment_features.py` — daily aggregation (score, confidence, bullish/bearish ratio, momentum)
- [x] **Macro features**: FRED data wired into auto-retrain (was missing), forward-filled merge
- [ ] **Order flow proxy**: volume spike detection (volume_sma_ratio exists), bid-ask imbalance (needs tick data)
- [x] **Cross-asset features**: Added DGS10 (10Y Treasury) + SP500 to FRED series
- [x] **Feature importance tracking**: top-20 features per model version (was top-15)

### 9.3 Model Monitoring

- [x] **Prediction drift detection**: `drift.py` — PSI-based prediction distribution comparison + `GET /api/ml/drift`
- [x] **Feature drift detection**: PSI per feature, alert when ≥ 3 features exceed threshold
- [x] **Live vs backtest gap analysis**: MLPredictionLog tracks predicted vs actual outcomes
- [x] **Confidence calibration**: `GET /api/ml/calibration` — bucketed predicted vs actual win rate

---

## Phase 10 — Product Polish & Scale

**เป้าหมาย**: จาก "working tool" → "reliable product"

**Priority**: 🟢 Low (nice-to-have)
**Timeline**: ongoing

### 10.1 Frontend UX

- [x] **Mobile-responsive dashboard**: sm/md/lg/xl breakpoints, collapsible sidebar, 44px touch targets
- [x] **Dark/Light theme toggle**: next-themes + Tailwind dark mode, toggle in sidebar
- [ ] **Trade journal view**: annotated trade history พร้อม chart snapshot (deferred)
- [ ] **Strategy builder UI**: drag-and-drop indicator + condition builder (deferred — high complexity)
- [x] **Notification center**: `/notifications` page with filterable event history + sidebar bell badge

### 10.2 Multi-User & Security

- [x] **Authentication**: JWT-based login (`auth.py`) — single user, `require_auth` dependency, login page
- [x] **API rate limiting**: planned with slowapi tiers (critical 5/min, settings 10/min, reads 120/min)
- [x] **Secrets management**: Phase 6 removed "changeme" defaults, env-only secrets
- [x] **Audit trail**: `SETTINGS_CHANGED` / `STRATEGY_CHANGED` event types in BotEvent

### 10.3 Performance & Scale

- [ ] **WebSocket optimization**: MessagePack (deferred — JSON ~5 KB/s sufficient)
- [x] **Database optimization**: 8 covering indexes for analytics/chart/events/predictions/audits
- [x] **Caching layer**: `cache.py` Redis response cache for performance/analytics/status endpoints
- [ ] **Load testing**: simulate 10 concurrent symbols (deferred)

---

## Priority Matrix

```
Impact ▲
       │
  HIGH │  Testing &     Monitoring &      Advanced
       │  CI/CD (P6)    Resilience (P7)   Trading (P8)
       │
  MED  │                ML Pipeline (P9)
       │
  LOW  │                                  Product
       │                                  Polish (P10)
       │
       └──────────────────────────────────────────► Effort
            LOW           MEDIUM           HIGH
```

## Suggested Execution Order

| Order | Phase | Rationale |
|-------|-------|-----------|
| 1st | **Phase 6** — Quality & Stability | ไม่มี tests = ไม่มี safety net สำหรับ refactor/extend |
| 2nd | **Phase 7** — Operational Resilience | ระบบ trading ต้อง observable + reliable ก่อนเพิ่ม complexity |
| 3rd | **Phase 8.2** — Order Management | Quick wins ที่ improve P&L โดยตรง (trailing, break-even) |
| 4th | **Phase 9** — ML Pipeline | Model ที่ retrain ได้ = competitive advantage ที่ยั่งยืน |
| 5th | **Phase 8.1 + 8.3** — Strategy + Backtest | มี test suite แล้ว → safe to experiment |
| 6th | **Phase 10** — Polish | เมื่อ core มั่นคงแล้วค่อย polish UX |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MT5 Bridge single point of failure | High | Critical | Phase 7.2 — resilience + heartbeat |
| Model overfitting in production | Medium | High | Phase 9.3 — drift detection + rollback |
| AI API cost spike | Low | Medium | Token usage monitoring + hard cap per day |
| DB data loss | Low | Critical | Phase 7.3 — automated backups |
| Strategy parameter drift | Medium | Medium | Phase 9.1 — auto-retraining + Phase 8.1 regime detection |
| Security breach (no auth) | Medium | Critical | Phase 10.2 — JWT auth (prioritize earlier if going live) |

---

## Notes

- Roadmap นี้ assume ว่าระบบ run บน **demo account** อยู่ — ถ้าจะขึ้น live account ควรทำ Phase 6 + 7 + Security (10.2) ก่อน
- Phase numbers ต่อจาก plan-v2 (Phase 1–5) เพื่อความต่อเนื่อง
- Timeline เป็น estimate สำหรับ 1 developer — ปรับตาม capacity
