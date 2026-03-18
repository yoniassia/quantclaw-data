# Data Control Centre (DCC) — Build Plan

**Owner:** Shay Heffets | **Builder:** Quant | **Date:** 2026-03-18
**URL:** data.quantclaw.org/dcc (new route within existing Next.js app)

---

## Architecture Context

- **DB:** quantclaw_data (PostgreSQL + TimescaleDB)
- **Tables:** modules (997), pipeline_runs (1658), quality_checks, alerts (2 active), data_points, symbol_universe, tag_definitions, module_tags
- **Tier distribution:** Gold: 516, Bronze: 459, Silver: 1, None: 21
- **Cadence distribution:** daily: 635, realtime: 219, monthly: 68, quarterly: 40, weekly: 25, 1h: 7, 1min: 3
- **Frontend:** Next.js 15 + TypeScript + Tailwind 4 + Zustand, port 3055
- **Theme:** Dark terminal aesthetic (JetBrains Mono, #0a0e14 background)
- **Existing components:** Terminal grid, panels, command bar

---

## Phase 1 — Foundation + Mission Control (Visibility)

Build the DCC route (`/dcc`) with:

1. **DCC Layout** — sidebar navigation (7 views), dark terminal theme
2. **API layer** — `/api/dcc/` endpoints hitting PostgreSQL directly
3. **Mission Control dashboard:**
   - Hero strip: total modules, tier distribution, alert counts, pipeline throughput
   - Module health heatmap (997 cells, color = tier/health, grouped by cadence)
   - Pipeline activity feed (recent runs, success/fail)
   - Alert feed (unresolved alerts)
4. **Zustand store** for DCC state

**API endpoints:**
- `GET /api/dcc/stats` — aggregate stats (module count, tier dist, alert count, run stats)
- `GET /api/dcc/modules` — paginated module list with filters
- `GET /api/dcc/pipeline/recent` — recent pipeline runs
- `GET /api/dcc/alerts` — alerts (filterable)

---

## Phase 2 — Module Explorer + Pipeline Monitor (Supervision)

1. **Module Explorer view:**
   - Filterable/searchable table of all 997 modules
   - Columns: name, cadence, tier, quality score, last run, error count, status
   - Filters: by tier, cadence, status, tags
   - Click → module detail panel (run history, config, quality checks)

2. **Pipeline Monitor view:**
   - Active/running pipelines
   - Queue (next scheduled)
   - Recent completions with status
   - Failure drill-down with error messages
   - Throughput chart (runs/hour over last 24h)

**API endpoints:**
- `GET /api/dcc/modules/:id` — module detail
- `GET /api/dcc/modules/:id/runs` — run history for module
- `GET /api/dcc/modules/:id/quality` — quality checks for module
- `GET /api/dcc/pipeline/active` — currently running pipelines
- `GET /api/dcc/pipeline/throughput` — runs/hour time series

---

## Phase 3 — Quality Console + Alert Center (Management)

1. **Quality Console:**
   - Overall quality score (weighted average)
   - Tier progression chart (movement between tiers over time)
   - Completeness/timeliness/accuracy breakdown
   - Worst performers (bottom 20 by quality)
   - Data gap calendar heatmap

2. **Alert Center:**
   - Active/resolved/all tabs
   - Filters: severity, category, module, date range
   - Acknowledge/resolve inline actions
   - Alert severity distribution chart

**API endpoints:**
- `GET /api/dcc/quality/overview` — quality metrics
- `GET /api/dcc/quality/worst` — worst performing modules
- `GET /api/dcc/alerts/stats` — alert distribution stats
- `PATCH /api/dcc/alerts/:id` — resolve/acknowledge alert

---

## Phase 4 — Source Health + Configuration (Advanced Ops)

1. **Source Health view:**
   - Table of data sources with uptime, module count, last fetch
   - Rate limit status per source
   - Dependency mapping (which sources feed which modules)

2. **Configuration view:**
   - Schedule editor (cron cadences)
   - Symbol universe management
   - System status (PostgreSQL, Redis, Kafka connection health)
   - API key status overview

**API endpoints:**
- `GET /api/dcc/sources` — data source health
- `GET /api/dcc/config/schedules` — cadence configuration
- `GET /api/dcc/config/universe` — symbol universe
- `GET /api/dcc/config/health` — system health checks
