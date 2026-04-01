# QuantClaw Data — AutoBuilder Scope
# Global Government Data Sources Integration

## Vision

Add **every programmatically accessible** central bank, securities regulator, and national statistics office data source from 36 countries into QuantClaw Data. This makes QuantClaw the most comprehensive open financial data platform — covering macro, monetary, filings, and economic indicators from every major economy.

## Target Countries

**EU (27):** Austria, Belgium, Bulgaria, Croatia, Cyprus, Czech Republic, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Ireland, Italy, Latvia, Lithuania, Luxembourg, Malta, Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia, Spain, Sweden

**Additional (9):** United States, United Kingdom, Australia, Singapore, UAE, Canada, Japan, Taiwan, China

## What Already Exists (DO NOT DUPLICATE)

These modules are already in `/modules/`. Enhance only if initiative explicitly says so.

### Central Banks (existing)
- `ecb.py` + 5 variants — ECB SDMX (EURIBOR, FX, HICP)
- `fred.py` + 20 variants — US Federal Reserve via FRED
- `bank_of_england.py` + 2 variants — BoE base rate, IADB
- `bank_of_japan*.py` — BoJ time series
- `bank_of_canada*.py` — BoC Valet API
- `rba_economic_data_feed.py` — Reserve Bank of Australia
- `bank_of_israel_dashboard.py` — Bank of Israel
- `bank_of_korea.py` — Bank of Korea
- `bis_*.py` — BIS credit, property, banking
- `pboc_*.py` — PBOC indicators

### Statistics Offices (existing)
- `eurostat.py` + 8 variants — Eurostat SDMX
- `bls.py` + 3 variants — US BLS
- `census*.py` + 5 variants — US Census Bureau
- `imf_*.py` — IMF SDMX
- `oecd*.py` — OECD stats
- `world_bank*.py` — World Bank indicators
- `abs_australia_stats.py` — Australian Bureau of Statistics
- `israel_cbs_statistics.py` — Israel CBS
- `singapore_dos.py` — Singapore Dept of Statistics
- `mas_singapore.py` — MAS Singapore

### Regulators (existing)
- `sec_edgar*.py` + 15 variants — US SEC
- `esma_regulatory_data*.py` — EU ESMA

## Module Pattern

Every new module MUST follow this structure:

```python
#!/usr/bin/env python3
"""
<Source Name> Module — Phase <N>

<Description of data source and what it provides>

Data Source: <URL>
Protocol: <REST/SDMX/CSV/PxWeb>
Auth: <None/API Key (free)/Registration>
Refresh: <Daily/Weekly/Monthly>
Coverage: <Country/Region>

Author: QUANTCLAW DATA Build Agent
Phase: <N>
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Configuration
BASE_URL = "<api_base>"
CACHE_DIR = Path(__file__).parent.parent / 'cache'

# Key indicators/series
INDICATORS = { ... }

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series."""
    ...

def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    ...

def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    ...

# CLI entry point
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        result = fetch_data(sys.argv[1])
    else:
        result = get_latest()
    print(json.dumps(result, indent=2, default=str))
```

## Acceptance Criteria

For each new module:
1. **Connects to real API** — no mocked data, no hallucinated endpoints
2. **Returns structured JSON** — date, value, indicator name, source
3. **Handles errors gracefully** — timeouts, 404s, rate limits
4. **Has caching** — 24h for most, 1h for FX/rates
5. **CLI-testable** — `python module.py [indicator]` works standalone
6. **No API key required** (preferred) or uses free-tier key from `.env`
7. **Documented** — docstring with source URL, protocol, refresh frequency

## Priority Tiers

### Tier A — SDMX/JSON APIs (highest priority, most automatable)
These have well-documented REST APIs returning structured data:
- Deutsche Bundesbank (SDMX REST)
- Banque de France Webstat (JSON REST, free registration)
- INSEE France (SDMX)
- ISTAT Italy (SDMX)
- CBS Netherlands StatLine (JSON API)
- Statistics Denmark DST (JSON API)
- SCB Sweden (PxWeb JSON API)
- Danmarks Nationalbank (StatBank JSON)
- Sveriges Riksbank (REST API)
- Statistics Finland (PxWeb API)
- NBP Poland (JSON API for FX/gold)
- Banco de España (JSON REST)
- Banco de Portugal BPstat (JSON-stat API)
- NBB Belgium (SDMX)
- Statistics Canada (WDS + SDMX)
- Bank of Canada extended (Valet enhancements)
- ONS UK (JSON API)
- e-Stat Japan (JSON API, needs app ID)
- CBC Taiwan (JSON API)
- Central Bank of Ireland (JSON-stat open data)
- CSO Ireland (PxWeb JSON)
- Bank of Japan enhanced (new 2026 API)

### Tier B — Good REST/download with parsing needed
- Czech National Bank ARAD (JSON, free key registration)
- Statistics Estonia (PxWeb)
- Statistics Austria (Open Data JSON)
- Statbel Belgium (CSV/JSON open data)
- INE Spain (JSON)
- BNR Romania (XML FX feeds)
- CZSO Czech Republic (Open Data)
- CBUAE + UAE Open Data (JSON portal)
- FCA UK register (JSON API, free key)
- EDINET Japan (API key, XBRL/CSV)
- ABS Australia enhanced (SDMX 2.1)
- RBA enhanced (CSV stable URLs)
- GENESIS-Online Germany (API with registration)

### Tier C — File-first sources (lower priority, parse CSV/Excel)
- OeNB Austria (table exports)
- BNB Bulgaria (Excel/CSV)
- HNB Croatia (Excel/CSV)
- Central Bank of Cyprus (Excel)
- Eesti Pank Estonia (CSV/Excel)
- Bank of Finland (CSV/Excel)
- Bank of Greece + ELSTAT (CSV)
- MNB Hungary + KSH (Excel/STADAT)
- Latvijas Banka (CSV/Excel)
- Lietuvos bankas (CSV)
- BCL Luxembourg (Excel)
- Central Bank of Malta (Excel)
- NBS Slovakia (Excel)
- Bank of Slovenia (CSV)
- CSB Latvia (PX/JSON)
- NSI Bulgaria (PC-Axis)
- STATEC Luxembourg (Excel)
- NSO Malta (Excel)

### Tier D — Fragmented/high-friction (lowest priority)
- NBS China stats.gov.cn (web portal, no standard API)
- CSRC China / SSE / SZSE (per-exchange, fragmented)
- Most EU national securities regulators (PDF-only for filings)

## Supranational Sources to Enhance

These already have basic modules — enhance with broader coverage:
- ECB: Add M1/M2/M3 monetary aggregates, bank lending survey, SAFE survey
- Eurostat: Add government finance, energy, environment datasets
- BIS: Add derivatives, FX turnover, payment statistics
- IMF: Add Financial Access Survey, CPIS, CDIS
- OECD: Add composite leading indicators, MEI, tax database
- World Bank: Add Doing Business, enterprise surveys, poverty data

## MCP Protection Rules (CRITICAL — from Shay Heffets)

Multiple production apps depend on the existing MCP server and its tool definitions.

**NEVER modify these files:**
- `mcp_server.py` — the MCP tool registry (other apps depend on exact tool names, params, and response shapes)
- `api_server.py` — the REST API server
- Any existing module in `modules/` unless the initiative explicitly says "enhance"

**ONLY add:**
- New standalone module files in `modules/` (e.g., `bundesbank_sdmx.py`)
- New modules are NOT automatically exposed via MCP — they must be manually registered later after review

**Why:** Shay has 4 apps consuming the MCP server. Changing tool names, parameter shapes, or response formats would break them. The autobuilder creates modules that work standalone (CLI + Python import). MCP registration is a separate, manual step done after human review.

## Non-Goals

- No scraping of PDF-only sources (Tier D regulators)
- No paid API subscriptions (free tier only)
- No breaking changes to existing modules or MCP/API server files
- No authentication that requires company/institutional access
- No modification to mcp_server.py or api_server.py
