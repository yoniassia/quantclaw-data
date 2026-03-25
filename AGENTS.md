# AGENTS.md — QuantClaw Data (DCC) 📊

Financial data pipeline & distribution center. 955+ data modules, gold/silver/bronze tier ingestion, REST API for all consumers.

**URL:** https://data.quantclaw.org/dcc | **Port:** 3055 | **PM2:** quantclaw-data

## Stack
- Python + FastAPI
- PostgreSQL for data storage
- 955+ modules (FRED, Yahoo, eToro SAPI, Financial Datasets, SEC EDGAR, etc.)
- Cron-based ingestion (4x daily for SAPI)

## Architecture
- DCC is the SINGLE SOURCE OF TRUTH for all financial data
- All consumer apps (TerminalX, AgentX, PICentral) pull from DCC — never directly from upstream APIs
- Three tiers: Gold (production-ready), Silver (validated), Bronze (raw)

## Key Paths
- `modules_v2/` — Data module implementations
- `modules_v2/etoro_sapi_instruments.py` — eToro SAPI integration (3,571+ symbols)

## Rules
- DCC-first: all data ingestion goes through DCC before reaching any consumer app
- No direct pipeline-to-frontend wiring
- Financial Datasets = primary, Yahoo = fallback
- Financial Datasets earnings endpoint is broken (404) — use alternatives

## MemClawz — Shared Memory (MANDATORY)

Endpoint: `http://127.0.0.1:3500/api/v1` | Agent ID: `quantclaw-data`

### Before ANY task:
```bash
curl -s "http://127.0.0.1:3500/api/v1/search?q=<task keywords>&agent_id=quantclaw-data&limit=5"
```

### After completing ANY significant work:
```bash
curl -s -X POST http://127.0.0.1:3500/api/v1/add \
  -H "Content-Type: application/json" \
  -d '{"content": "<what was done>", "agent_id": "quantclaw-data", "memory_type": "<decision|procedure|event|insight>"}'
```
