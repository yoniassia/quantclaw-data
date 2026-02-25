# Global Health Impact Monitor (Phase 199)

**Status:** ✅ DONE  
**Lines of Code:** 556  
**Category:** Alternative Data  
**Update Frequency:** Weekly

## Overview

Comprehensive global health surveillance and pandemic economic impact monitoring system. Tracks disease outbreaks worldwide and measures their economic impact through key indicators.

## Data Sources

### Health Data
- **WHO Disease Outbreak News** - Global disease surveillance
- **Google Trends** - Search interest in health crises (proxy data)
- **Cached Outbreak Database** - Recent outbreaks with case counts, deaths, and alert levels

### Economic Impact Data
- **FRED API** (Federal Reserve Economic Data)
  - TSA Throughput - Air travel checkpoint numbers
  - Retail Sales - Retail and food services sales
  - Unemployment Rate - Civilian unemployment
  - Initial Jobless Claims - Weekly unemployment claims
  - Load Factor - Airline capacity utilization
  - Hotel Occupancy Rate - Hospitality sector health

## CLI Commands

### 1. health-outbreaks
Track current disease outbreaks worldwide

```bash
python cli.py health-outbreaks [OPTIONS]

Options:
  --country TEXT     Filter by country name
  --disease TEXT     Filter by disease name (e.g., Dengue, Cholera, Mpox)
  --days INTEGER     Lookback period in days (default: 90)
  --json             Output raw JSON
```

**Example:**
```bash
# View recent outbreaks in Africa
python cli.py health-outbreaks --days 800

# Filter for specific disease
python cli.py health-outbreaks --disease Cholera --days 365

# Get JSON output
python cli.py health-outbreaks --json
```

**Output Includes:**
- Total cases and deaths
- Case fatality rate (CFR)
- WHO alert levels (HIGH/MEDIUM/LOW)
- Countries affected
- Search trend data (when available)

### 2. pandemic-impact
Analyze economic impact from pandemics and health crises

```bash
python cli.py pandemic-impact [OPTIONS]

Options:
  --metric TEXT      Metric type: travel, retail, unemployment, all (default: all)
  --country TEXT     Country code (default: US)
  --start TEXT       Start date (YYYY-MM-DD)
  --end TEXT         End date (YYYY-MM-DD)
  --json             Output raw JSON
```

**Example:**
```bash
# View all economic indicators for past year
python cli.py pandemic-impact

# Focus on travel sector
python cli.py pandemic-impact --metric travel

# Unemployment indicators
python cli.py pandemic-impact --metric unemployment

# Custom date range
python cli.py pandemic-impact --start 2020-01-01 --end 2021-12-31
```

**Output Includes:**
- Current vs. baseline values for each indicator
- Percentage change over period
- Trend direction (IMPROVING/WORSENING/STABLE)
- Composite impact score with interpretation

### 3. health-monitor
Global health surveillance dashboard with risk assessment

```bash
python cli.py health-monitor [OPTIONS]

Options:
  --region TEXT            Region: global, africa, asia, americas, europe (default: global)
  --alert-threshold TEXT   Min alert level: HIGH, MEDIUM, LOW (default: MEDIUM)
  --json                   Output raw JSON
```

**Example:**
```bash
# Global surveillance
python cli.py health-monitor

# Africa region with high-priority alerts only
python cli.py health-monitor --region africa --alert-threshold HIGH

# Americas region
python cli.py health-monitor --region americas
```

**Output Includes:**
- Overall risk assessment (CRITICAL/HIGH/ELEVATED/MODERATE)
- Disease rankings by cases
- Case fatality rates
- Active outbreaks by region
- High-priority outbreak counts

## MCP Tools

### get_health_outbreaks
```python
{
  "name": "get_health_outbreaks",
  "description": "Track current disease outbreaks worldwide from WHO and other sources",
  "parameters": {
    "country": "Optional country name to filter outbreaks",
    "disease": "Optional disease name (e.g., Dengue, Cholera, Mpox)",
    "days": "Lookback period in days (default 90)"
  }
}
```

### get_pandemic_impact
```python
{
  "name": "get_pandemic_impact",
  "description": "Analyze economic impact from pandemics using FRED indicators",
  "parameters": {
    "metric": "Type: travel, retail, unemployment, or all (default all)",
    "country": "Country code (default US)",
    "start_date": "Start date (YYYY-MM-DD)",
    "end_date": "End date (YYYY-MM-DD)"
  }
}
```

### get_health_monitor
```python
{
  "name": "get_health_monitor",
  "description": "Global health surveillance dashboard with risk assessment",
  "parameters": {
    "region": "Region: global, africa, asia, americas, europe (default global)",
    "alert_threshold": "Min alert level: HIGH, MEDIUM, LOW (default MEDIUM)"
  }
}
```

## Known Disease Outbreaks (Sample Data)

| Date    | Disease        | Countries                              | Cases   | Deaths | Alert Level |
|---------|----------------|----------------------------------------|---------|--------|-------------|
| 2024-02 | Dengue         | Brazil, Argentina, Peru                | 400,000 | 89     | MEDIUM      |
| 2024-01 | Cholera        | Zimbabwe, Zambia, Mozambique           | 18,000  | 400    | HIGH        |
| 2023-12 | Mpox           | DRC, Nigeria, Cameroon                 | 5,200   | 12     | MEDIUM      |
| 2023-09 | Marburg Virus  | Equatorial Guinea, Tanzania            | 23      | 11     | HIGH        |

## Risk Assessment Methodology

### Composite Impact Score
Calculated from economic indicators:
- **SEVERE NEGATIVE IMPACT**: < -10%
- **NEGATIVE IMPACT**: -10% to -5%
- **RECOVERING**: +5% to +10%
- **RECOVERED**: > +10%
- **STABLE**: -5% to +5%

### Health Risk Levels
- **CRITICAL**: 3+ high alerts OR 500K+ cases
- **HIGH**: 1+ high alert OR 100K+ cases
- **ELEVATED**: 10K+ total cases
- **MODERATE**: < 10K total cases

## Technical Details

### API Endpoints
- **FRED API**: `https://api.stlouisfed.org/fred/series/observations`
  - Public API key included for economic data
  - Rate limits: Standard FRED API limits apply

### Data Refresh
- **Health Outbreaks**: Update on-demand (cached data structure)
- **Economic Indicators**: FRED updates vary by series (daily to monthly)
- **Search Trends**: Proxy data included in module

### Error Handling
- Graceful fallback if FRED API unavailable
- Returns partial data if some indicators fail
- Clear error messages in JSON output

## Use Cases

### 1. Pandemic Early Warning
Monitor disease outbreaks across regions to identify emerging threats before they become global pandemics.

### 2. Economic Impact Assessment
Quantify the economic toll of health crises on travel, retail, employment sectors.

### 3. Investment Risk Analysis
Factor health crisis risks into portfolio decisions for affected sectors (airlines, hospitality, healthcare).

### 4. Geographic Risk Scoring
Assess business continuity risks for operations in outbreak-affected regions.

### 5. Policy Response Tracking
Monitor how economic indicators respond to public health interventions.

## Future Enhancements

- [ ] Real-time WHO API integration (when public API available)
- [ ] CDC Wonder database integration
- [ ] Hospital capacity tracking
- [ ] Vaccine distribution monitoring
- [ ] Supply chain disruption metrics
- [ ] Additional countries' economic indicators
- [ ] Machine learning outbreak prediction
- [ ] Real-time news sentiment analysis

## Notes

- **Mock Data**: Current outbreak database uses recent historical data (2023-2024)
- **Date Filters**: Use longer lookback periods (--days 800) to capture historical outbreaks
- **Economic Data**: US-focused due to FRED data availability; future expansion planned
- **Free APIs**: All data sources are free/public - no API keys required except FRED (public key included)

## Testing

```bash
# Test all commands
python cli.py health-outbreaks --help
python cli.py pandemic-impact --help
python cli.py health-monitor --help

# Functional tests
python cli.py health-outbreaks --days 800
python cli.py pandemic-impact --metric unemployment
python cli.py health-monitor --region africa --alert-threshold HIGH

# JSON output tests
python cli.py health-outbreaks --json | jq
python cli.py health-monitor --json | jq '.risk_assessment'
```

## Integration

Add to your analysis workflow:

```python
from health_impact import get_health_outbreaks, get_pandemic_impact, get_health_monitor

# Check global outbreak status
outbreaks = get_health_outbreaks(days=90)
print(f"High alerts: {outbreaks['summary']['high_alert_count']}")

# Assess pandemic economic impact
impact = get_pandemic_impact(metric='all')
print(f"Composite score: {impact['composite_score']['value']}")

# Regional surveillance
africa_risk = get_health_monitor(region='africa', alert_threshold='HIGH')
print(f"Risk level: {africa_risk['risk_assessment']['level']}")
```

---

**Built:** 2026-02-25  
**Author:** QuantClaw Development Team  
**License:** MIT
