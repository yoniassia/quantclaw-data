# Global Government Bond Yields — Phase 107

## Overview
Comprehensive 10-year government bond yield data for 40+ countries via FRED (Federal Reserve Economic Data).

## Features
- ✅ 10Y yields for 40+ countries (G7, BRICS, Asia-Pacific, Europe, LatAm, Middle East)
- ✅ US Treasury yield curve (1M to 30Y)
- ✅ US TIPS real yields (inflation-adjusted)
- ✅ US breakeven inflation rates (market-implied inflation expectations)
- ✅ Yield spread calculations vs any base country
- ✅ Historical time series data
- ✅ Daily updates

## Data Coverage

### Regions
- **G7**: US, Germany, Japan, UK, France, Italy, Canada
- **Europe**: Spain, Portugal, Greece, Netherlands, Belgium, Austria, Switzerland, Norway, Sweden, Denmark, Poland
- **Asia-Pacific**: Australia, New Zealand, South Korea, Singapore, Hong Kong, China, India
- **Latin America**: Mexico, Brazil, Chile, Colombia
- **Middle East**: Israel, Turkey
- **Africa**: South Africa
- **Other**: Russia

### Series Types
1. **10Y Yields**: Benchmark 10-year government bond yields
2. **US Yield Curve**: 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y
3. **US Real Yields**: TIPS yields for 5Y, 7Y, 10Y, 20Y, 30Y
4. **Breakeven Inflation**: 5Y, 10Y, 30Y market-implied inflation expectations

## Requirements

### FRED API Key (Required)
Register for a free API key at: https://fred.stlouisfed.org/

Set environment variable:
```bash
export FRED_API_KEY="your_api_key_here"
```

**Limits**:
- Free tier: 120 requests/minute, 10 years of data
- No credit card required

## CLI Usage

```bash
# List all available countries
python3 cli.py list-countries

# Get 10Y yield for a country
python3 cli.py yield US
python3 cli.py yield DE
python3 cli.py yield JP

# Compare yields across countries
python3 cli.py compare US DE JP GB FR IT CA

# Calculate spreads vs base country
python3 cli.py spreads US        # All countries vs US
python3 cli.py spreads DE        # All countries vs Germany

# US Treasury yield curve
python3 cli.py us-curve

# US TIPS real yields
python3 cli.py us-real

# US breakeven inflation
python3 cli.py us-breakeven

# Comprehensive data for any country (extended for US)
python3 cli.py comprehensive US
python3 cli.py comprehensive DE
```

## MCP Tools

### global_bonds_list_countries
List all 40+ countries with bond yield data.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "countries": [
    {"code": "US", "name": "United States 10Y Treasury", "series_id": "DGS10"},
    {"code": "DE", "name": "Germany 10Y Bund", "series_id": "IRLTLT01DEM156N"}
  ],
  "count": 40
}
```

### global_bonds_yield
Get 10-year yield for a specific country with historical data.

**Parameters**:
- `country_code` (string, required): 2-letter country code (e.g., US, DE, JP)
- `days` (integer, optional): Number of days of historical data (default 30)

**Returns**:
```json
{
  "success": true,
  "data": {
    "country": "US",
    "country_name": "United States 10Y Treasury",
    "series_id": "DGS10",
    "latest_date": "2026-02-24",
    "yield": 4.32,
    "change_1d": -0.05,
    "change_1w": 0.12,
    "change_1m": -0.23,
    "historical": [...]
  }
}
```

### global_bonds_compare
Compare 10Y yields across multiple countries.

**Parameters**:
- `country_codes` (array, required): List of 2-letter country codes

**Returns**:
```json
{
  "success": true,
  "comparison": [
    {
      "country": "BR",
      "country_name": "Brazil 10Y Bond",
      "yield": 12.45,
      "change_1m": 0.34
    },
    {
      "country": "US",
      "country_name": "United States 10Y Treasury",
      "yield": 4.32,
      "change_1m": -0.23
    }
  ]
}
```

### global_bonds_spreads
Calculate yield spreads relative to a base country.

**Parameters**:
- `base_country` (string, optional): Base country code (default "US")

**Returns**:
```json
{
  "success": true,
  "spreads": [
    {
      "country": "BR",
      "country_name": "Brazil 10Y Bond",
      "yield": 12.45,
      "spread_vs_base": 8.13,
      "spread_bps": 813,
      "base_country": "US",
      "base_yield": 4.32
    }
  ]
}
```

### global_bonds_us_curve
Get full US Treasury yield curve.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "data": {
    "date": "2026-02-24",
    "curve": {
      "1M": 4.55,
      "3M": 4.48,
      "2Y": 4.21,
      "10Y": 4.32,
      "30Y": 4.52
    },
    "slope_2s10s": 0.11,
    "slope_3m10y": -0.16,
    "inverted_2s10s": false,
    "inverted_3m10y": true
  }
}
```

### global_bonds_us_real
Get US TIPS real yields (inflation-adjusted).

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "data": {
    "date": "2026-02-24",
    "real_yields": {
      "5Y": 1.85,
      "7Y": 1.92,
      "10Y": 2.02,
      "20Y": 2.15,
      "30Y": 2.18
    }
  }
}
```

### global_bonds_us_breakeven
Get US breakeven inflation rates (market-implied inflation expectations).

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "data": {
    "date": "2026-02-24",
    "breakeven_inflation": {
      "5Y": 2.30,
      "10Y": 2.25,
      "30Y": 2.20
    }
  }
}
```

### global_bonds_comprehensive
Get comprehensive bond data for any country (extended data for US).

**Parameters**:
- `country_code` (string, optional): 2-letter country code (default "US")

**Returns**: For US, includes 10Y yield + yield curve + real yields + breakeven inflation. For other countries, only 10Y yield with extended history.

## Use Cases

### 1. Central Bank Policy Analysis
Monitor global interest rate differentials to assess monetary policy stance across countries.

```bash
python3 cli.py compare US DE JP GB FR
```

### 2. Currency Trade Setup
Wide yield spreads often drive carry trades. High-yield countries (BR, TR, ZA) vs low-yield (JP, CH).

```bash
python3 cli.py spreads US
```

### 3. Recession Signals
Inverted yield curves (2s10s, 3m10y) historically precede recessions.

```bash
python3 cli.py us-curve
```

### 4. Inflation Expectations
Breakeven rates reveal market-implied inflation forecasts.

```bash
python3 cli.py us-breakeven
```

### 5. Risk-On/Risk-Off Regime
Rising EM spreads vs DM = risk-off. Compressing spreads = risk-on.

```bash
python3 cli.py spreads US > risk_monitor.json
```

## Data Source
All data via **FRED (Federal Reserve Economic Data)**:
- API: https://api.stlouisfed.org/fred
- Coverage: Daily updates for most series
- Latency: T+0 to T+1 depending on source

## Phase Info
- **Phase**: 107
- **Category**: Global Macro
- **Status**: Done
- **LOC**: 536
- **Data Sources**: FRED API (40+ bond series)

## Author
QuantClaw Data Build Agent — Phase 107 (Global Government Bond Yields)
