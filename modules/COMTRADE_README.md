# UN Comtrade Trade Flows — Phase 103

## Overview

Bilateral trade flows and commodity-level import/export data for 200+ countries via the UN Comtrade API.

**Data Source:** comtradeapi.un.org  
**Coverage:** 200+ countries, 5,000+ commodity codes (HS classification)  
**Refresh:** Monthly  
**API Key:** Required for trade data endpoints (free tier available)

## Features

### Reference Data (No API Key Required)
- **Reporters:** List of 255 reporting countries
- **Partners:** Trade partner countries (same as reporters)
- **Commodities:** 5,000+ HS commodity codes (2-digit, 4-digit, 6-digit)
- **Search:** Search countries and commodities by name or code

### Trade Data (API Key Required)
- **Bilateral Trade:** Country-to-country trade flows
- **Top Partners:** Identify major import/export partners
- **Trade Balance:** Calculate exports - imports
- **Commodity Trade:** Specific commodity flows (e.g., oil, machinery)
- **Concentration Analysis:** Herfindahl-Hirschman Index (HHI) for trade concentration
- **Dependencies:** Identify critical trade dependencies (> threshold%)

## CLI Usage

### Reference Data Commands (Work Without API Key)

```bash
# List all reporting countries
python cli.py reporters

# List partner countries
python cli.py partners

# List commodity codes (2-digit HS codes)
python cli.py commodities 2

# Search for a country
python cli.py search-country china
python cli.py search-country USA

# Search for commodities
python cli.py search-commodity machinery
python cli.py search-commodity oil
```

### Trade Data Commands (Require API Key)

Set your API key as an environment variable:
```bash
export COMTRADE_API_KEY="your-api-key-here"
```

Get your free API key at: https://comtradeplus.un.org/

```bash
# Bilateral trade (USA imports from China, 2023)
python cli.py bilateral USA CHN 2023 M

# Bilateral exports (USA exports to China, 2023)
python cli.py bilateral USA CHN 2023 X

# Top import partners (USA, 2023, top 10)
python cli.py top-partners USA M 2023 10

# Top export partners (China, 2023, top 20)
python cli.py top-partners CHN X 2023 20

# Trade balance (USA with all partners, 2023)
python cli.py trade-balance USA

# Trade balance (USA with China specifically, 2023)
python cli.py trade-balance USA CHN 2023

# Commodity trade (USA machinery imports, 2023)
python cli.py commodity-trade USA 84 2023 M

# Trade concentration analysis (China exports, 2023)
python cli.py concentration CHN 2023 X

# Identify critical dependencies (USA, >10% threshold, 2023)
python cli.py dependencies USA 10 2023
```

## Flow Types

- **M**: Imports
- **X**: Exports
- **RM**: Re-Imports
- **RX**: Re-Exports

## Example Use Cases

### 1. Analyze US-China Trade
```bash
# US imports from China
python cli.py bilateral USA CHN 2023 M

# US exports to China
python cli.py bilateral USA CHN 2023 X

# Trade balance
python cli.py trade-balance USA CHN 2023
```

### 2. Identify Export Dependencies
```bash
# Find countries where >15% of exports go to single partner
python cli.py dependencies DEU 15 2023

# Analyze export concentration risk
python cli.py concentration DEU 2023 X
```

### 3. Track Commodity Flows
```bash
# Search for oil commodity codes
python cli.py search-commodity oil

# Get oil import data for country
python cli.py commodity-trade USA 2709 2023 M
```

### 4. Compare Trade Partners
```bash
# Top import sources
python cli.py top-partners USA M 2023 10

# Top export destinations
python cli.py top-partners USA X 2023 10
```

## MCP Tools

### `comtrade_reporters`
Get list of reporting countries.

### `comtrade_search_country`
Search for country by name or code.

**Parameters:**
- `query` (string, required): Country name or ISO code

### `comtrade_search_commodity`
Search for commodity by description or HS code.

**Parameters:**
- `query` (string, required): Commodity description or HS code

### `comtrade_bilateral_trade`
Get bilateral trade flows between two countries.

**Parameters:**
- `reporter` (string, required): Reporter country code
- `partner` (string, required): Partner country code
- `year` (integer, optional): Year (default: previous year)
- `flow` (string, optional): M or X (default: M)
- `api_key` (string, optional): UN Comtrade API key

### `comtrade_top_partners`
Get top trade partners for a country.

**Parameters:**
- `reporter` (string, required): Reporter country code
- `flow` (string, optional): M or X (default: M)
- `year` (integer, optional): Year
- `limit` (integer, optional): Number of partners (default: 20)
- `api_key` (string, optional): UN Comtrade API key

### `comtrade_trade_balance`
Calculate trade balance.

**Parameters:**
- `reporter` (string, required): Reporter country code
- `partner` (string, optional): Partner country code (default: all)
- `year` (integer, optional): Year
- `api_key` (string, optional): UN Comtrade API key

### `comtrade_concentration`
Analyze trade concentration (HHI).

**Parameters:**
- `reporter` (string, required): Reporter country code
- `year` (integer, optional): Year
- `flow` (string, optional): M or X (default: X)
- `api_key` (string, optional): UN Comtrade API key

**Returns:**
- `hhi`: Herfindahl-Hirschman Index (0-10000)
- `concentration_level`: Low/Moderate/High
- `top_partners`: Top 10 partners with shares
- `top_3_share`: Combined share of top 3 partners

### `comtrade_dependencies`
Identify critical trade dependencies.

**Parameters:**
- `reporter` (string, required): Reporter country code
- `threshold` (number, optional): Min % to flag as dependency (default: 10)
- `year` (integer, optional): Year
- `api_key` (string, optional): UN Comtrade API key

## HS Commodity Classification

The Harmonized System (HS) is a standardized numerical method of classifying traded products:

- **2-digit**: Section level (e.g., 84 = Machinery)
- **4-digit**: Heading level (e.g., 8471 = Computers)
- **6-digit**: Subheading level (e.g., 847130 = Portable computers)

## Major Commodity Categories

- **01-05**: Live Animals & Animal Products
- **06-14**: Vegetable Products
- **25-27**: Mineral Products (includes oil, gas, coal)
- **28-38**: Chemicals
- **39-40**: Plastics & Rubber
- **44-46**: Wood Products
- **50-63**: Textiles
- **68-70**: Stone, Glass & Ceramics
- **71**: Precious Stones & Metals
- **72-83**: Base Metals
- **84-85**: Machinery & Electrical Equipment
- **86-89**: Transportation Equipment
- **90-92**: Precision Instruments

## API Rate Limits

- **Free Tier**: 100 requests/hour, 1,000/month
- **Premium Tier**: Higher limits available

## Trade Concentration Interpretation

**Herfindahl-Hirschman Index (HHI):**
- **< 1000**: Low concentration (diversified)
- **1000-1800**: Moderate concentration
- **> 1800**: High concentration (risky)

High concentration means a country is heavily dependent on a few partners — strategic risk if trade is disrupted.

## Data Quality Notes

- Most recent data typically lags by 3-6 months
- Some countries report quarterly, others monthly
- Missing data for countries with trade restrictions
- Re-exports (RX) not reported by all countries

## Getting Started

1. **Get API Key** (for trade data):
   - Visit: https://comtradeplus.un.org/
   - Sign up for free account
   - Get subscription key from dashboard

2. **Set Environment Variable**:
   ```bash
   export COMTRADE_API_KEY="your-key"
   ```

3. **Test Reference Data** (no key needed):
   ```bash
   python cli.py search-country usa
   python cli.py commodities 2
   ```

4. **Test Trade Data** (requires key):
   ```bash
   python cli.py top-partners USA X 2023 10
   ```

## Python Module API

```python
from modules.comtrade import (
    get_reporters,
    search_country,
    get_bilateral_trade,
    get_top_trade_partners,
    analyze_trade_concentration,
    get_trade_dependencies
)

# Search for country
matches = search_country('china')

# Get bilateral trade (requires API key)
trade = get_bilateral_trade(
    reporter='USA',
    partner='CHN',
    year=2023,
    flow='M',
    api_key='your-key'
)

# Analyze concentration
concentration = analyze_trade_concentration(
    reporter='CHN',
    year=2023,
    flow='X',
    api_key='your-key'
)
```

## Build Info

- **Phase:** 103
- **Category:** Global Macro
- **Lines of Code:** 834
- **Status:** Done ✅
