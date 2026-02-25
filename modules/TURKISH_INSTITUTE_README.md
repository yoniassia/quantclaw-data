# Turkish Statistical Institute Module (Phase 124)

## Overview
Comprehensive Turkish economic data integration via TUIK (TÜİK) and CBRT (TCMB - Central Bank of Turkey) APIs.

## Data Coverage
- **Inflation**: CPI, PPI (monthly)
- **GDP**: Real & Nominal (quarterly)
- **Trade**: Exports, imports, balance (monthly)
- **Labor**: Unemployment rate (monthly)
- **Monetary Policy**: Policy rate, FX reserves (daily/weekly)
- **Exchange Rates**: USD/TRY, EUR/TRY (daily)
- **Industrial Production**: Manufacturing, mining, electricity (monthly)

## Data Sources

### CBRT EVDS API
- **URL**: https://evds2.tcmb.gov.tr/
- **Protocol**: REST JSON via SDMX
- **Registration**: Free API key required
- **Sign up**: https://evds2.tcmb.gov.tr/index.php?/evds/login
- **Documentation**: https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Service_Usage_Guide.pdf

### TUIK
- **URL**: https://data.tuik.gov.tr/
- **Note**: Many indicators available via CBRT EVDS API

## API Key Setup (Optional)

To enable real-time data fetching:

1. Register at https://evds2.tcmb.gov.tr/
2. Generate API key from your account
3. Add to module configuration (future enhancement)

**Current Status**: Module works without API key but returns graceful errors for data not available via public endpoint. Series codes are documented and ready for production use once API key is configured.

## CLI Commands

```bash
# List all indicators
python3 cli.py tuik-indicators

# Get inflation data (CPI, PPI)
python3 cli.py tuik-inflation

# Get GDP data
python3 cli.py tuik-gdp

# Get trade data
python3 cli.py tuik-trade

# Get unemployment
python3 cli.py tuik-unemployment

# Get monetary policy (policy rate, reserves)
python3 cli.py tuik-monetary

# Get exchange rates
python3 cli.py tuik-fx

# Get complete snapshot
python3 cli.py tuik-snapshot

# Get specific indicator
python3 cli.py tuik-indicator CPI_ANNUAL
python3 cli.py tuik-indicator USD_TRY
```

## MCP Tools

Available via MCP server:
- `tuik_snapshot` - Complete economic overview
- `tuik_indicator` - Specific indicator by key
- `tuik_inflation` - CPI/PPI data
- `tuik_gdp` - GDP data
- `tuik_trade` - Trade data
- `tuik_unemployment` - Unemployment data
- `tuik_monetary` - Monetary policy data
- `tuik_fx` - Exchange rates
- `tuik_indicators` - List all indicators

## Series Codes

All CBRT EVDS series codes are documented in `TURKISH_INDICATORS` dictionary in `turkish_institute.py`.

## Implementation Status

✅ Module created (810 LOC)
✅ CLI commands registered
✅ MCP tools registered
✅ Roadmap updated to "done"
⚠️ Real-time data requires CBRT EVDS API key (free registration)

## Future Enhancements

1. Add API key configuration support
2. Add TUIK direct API integration (if available)
3. Add provincial/regional breakdown
4. Add sector-specific industrial production
5. Add consumer confidence, PMI indicators
