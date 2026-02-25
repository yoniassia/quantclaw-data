# World Bank Open Data Module (Phase 94)

## Overview
Comprehensive economic indicators for 217 countries via World Bank API.

**Data Source:** api.worldbank.org/v2  
**Refresh:** Weekly  
**Coverage:** 217 countries, 60+ years of historical data  
**Lines of Code:** 656

## Available Indicators

- **GDP**: GDP (current US$)
- **GDP_GROWTH**: GDP growth (annual %)
- **GNI**: GNI (current US$)
- **GNI_PER_CAPITA**: GNI per capita
- **INFLATION**: Consumer price inflation (annual %)
- **FDI**: Foreign direct investment (% of GDP)
- **FDI_NET_INFLOWS**: FDI net inflows (current US$)
- **POVERTY**: Poverty headcount ratio at $2.15/day
- **UNEMPLOYMENT**: Unemployment rate
- **TRADE**: Trade (% of GDP)
- **DEBT**: Government debt (% of GDP)
- **POPULATION**: Total population

## CLI Commands

### 1. Country Profile
Get comprehensive economic profile for a country:
```bash
python cli.py country-profile USA
python cli.py country-profile CHN --indicators GDP,INFLATION,FDI
```

### 2. List Countries
List all countries with optional region filter:
```bash
python cli.py countries
python cli.py countries --region EAS
```

### 3. Get Indicator
Get specific indicator for a country:
```bash
python cli.py indicator USA GDP
python cli.py indicator CHN INFLATION
```

### 4. Compare Countries
Compare indicator across multiple countries:
```bash
python cli.py compare USA,CHN,JPN,DEU,GBR --indicator GDP
python cli.py compare USA,CHN --indicator GDP_GROWTH
```

### 5. Search Countries
Search for countries by name:
```bash
python cli.py search "United"
python cli.py search "Germany"
```

### 6. Regional Aggregates
Get aggregated data for a region:
```bash
python cli.py regional EAS --indicator GDP_GROWTH
python cli.py regional NAC --indicator INFLATION
```

### 7. List Indicators
List all available indicators:
```bash
python cli.py indicators
```

## World Bank Regions

- **EAS**: East Asia & Pacific
- **ECS**: Europe & Central Asia
- **LCN**: Latin America & Caribbean
- **MEA**: Middle East & North Africa
- **NAC**: North America
- **SAS**: South Asia
- **SSA**: Sub-Saharan Africa

## MCP Server Tools

The module is exposed via MCP server with the following tools:

1. **worldbank_country_profile** - Get comprehensive country economic profile
2. **worldbank_countries** - List all countries (with optional region filter)
3. **worldbank_indicator** - Get specific indicator for a country
4. **worldbank_compare** - Compare countries on specific indicator
5. **worldbank_search** - Search countries by name
6. **worldbank_regional** - Get regional aggregate data
7. **worldbank_indicators** - List all available indicators

### MCP Server Usage

List all tools:
```bash
python mcp_server.py list-tools
```

Call a tool:
```bash
python mcp_server.py call worldbank_country_profile '{"country_code": "USA"}'
python mcp_server.py call worldbank_search '{"query": "Germany"}'
```

Start MCP server:
```bash
python mcp_server.py serve
```

## Example Output

### Country Profile
```json
{
  "success": true,
  "country": "United States",
  "country_code": "USA",
  "region": "North America",
  "income_level": "High income",
  "capital": "Washington D.C.",
  "indicators": {
    "GDP": {
      "name": "GDP (current US$)",
      "latest_value": 25462700000000,
      "latest_year": 2022,
      "yoy_change": 2100000000000,
      "yoy_change_pct": 8.99
    },
    "INFLATION": {
      "name": "Inflation, consumer prices (annual %)",
      "latest_value": 2.95,
      "latest_year": 2024,
      "yoy_change": -1.17,
      "yoy_change_pct": -28.35
    }
  }
}
```

## Implementation Notes

- **Rate Limiting**: 0.1s sleep between API calls to be nice to World Bank API
- **Pagination**: Handles World Bank's paginated responses (500 items per page)
- **Error Handling**: Graceful fallbacks when data is unavailable
- **Data Quality**: Filters out regional aggregates to show only real countries
- **Historical Data**: Provides YoY change calculations automatically

## Future Enhancements

- Cache frequently accessed data locally
- Add visualization endpoints (charts, maps)
- Implement bulk data download for offline analysis
- Add more advanced comparative analytics
- Integration with other macro data sources (IMF, OECD)

## Author
QUANTCLAW DATA Build Agent  
Phase: 94  
Built: 2026-02-25
