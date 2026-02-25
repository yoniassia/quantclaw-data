# Phase 195: Semiconductor Chip Data Module

## Overview
Complete semiconductor industry data module providing monthly sales, market forecasts, and fab utilization metrics. Tracks the global $527B semiconductor market with regional breakdowns, segment analysis, and company-level insights.

## Data Sources
- **FRED API**: Industrial Production Index (Semiconductors), PPI, Capacity Utilization
- **Public SIA Reports**: Semiconductor Industry Association market data
- **WSTS Forecasts**: World Semiconductor Trade Statistics (public releases)
- **Industry Reports**: TSMC, Samsung, Intel earnings and fab utilization disclosures

## Module: `semiconductor_chip.py`
**Lines of Code:** 506

### Key Features
1. **Monthly Sales Data**: Regional chip sales by market (Americas, Europe, Japan, Asia-Pacific)
2. **Market Forecasts**: WSTS multi-year forecasts with segment and regional breakdowns
3. **Fab Utilization**: Industry-wide, regional, and company-specific utilization rates
4. **Market Intelligence**: Top companies, key trends, supply/demand indicators

### Data Structures

#### Regional Markets
- **Americas** (23% share): US, Canada, Mexico, Brazil
- **Europe** (9% share): Germany, France, UK, Netherlands, Ireland
- **Japan** (8% share): Japan
- **Asia-Pacific** (60% share): China, Taiwan, South Korea, Singapore, Malaysia, India

#### Semiconductor Segments
- **Memory** (25%): DRAM, NAND Flash, NOR Flash
- **Logic** (30%): Microprocessors, GPUs, FPGAs
- **Analog** (15%): Power Management, Amplifiers, Converters
- **MPU** (18%): Microcontrollers, DSPs, Embedded
- **Discrete** (12%): MOSFETs, IGBTs, Power Diodes

#### Top Companies (2023 Revenue)
1. **TSMC**: $69.3B (Foundry, Asia-Pacific)
2. **Nvidia**: $60.9B (Fabless, Americas)
3. **Intel**: $54.2B (Logic, Americas)
4. **Samsung**: $47.0B (Memory, Asia-Pacific)
5. **Qualcomm**: $35.8B (Fabless, Americas)
6. **Broadcom**: $35.8B (Fabless, Americas)
7. **SK Hynix**: $26.9B (Memory, Asia-Pacific)
8. **AMD**: $22.7B (Fabless, Americas)
9. **TI**: $17.5B (Analog, Americas)
10. **Micron**: $15.5B (Memory, Americas)

### Fab Utilization Benchmarks
- **Healthy Min**: 80%
- **Optimal**: 85%
- **Constraint**: 95%
- **Current Est**: 77% (Q4 2023)
- **2022 Avg**: 84%
- **2023 Avg**: 75% (inventory correction)

## CLI Commands

### 1. Chip Sales
```bash
python cli.py chip-sales [region] [months]
```
**Parameters:**
- `region`: all, americas, europe, japan, asia_pacific (default: all)
- `months`: Number of months to retrieve (default: 12)

**Examples:**
```bash
python cli.py chip-sales americas 6
python cli.py chip-sales asia_pacific 12
python cli.py chip-sales all 24
```

**Output:**
```json
{
  "query": {
    "region": "americas",
    "months": 6
  },
  "market_size": {
    "total_market_size_bn": 527.0,
    "yoy_growth_pct": -8.2,
    "forecast_2024_bn": 576.0
  },
  "data": [
    {
      "date": "2023-10-01",
      "production_index": 98.5,
      "estimated_sales_bn": 43.2,
      "regional_sales_bn": 9.9,
      "regional_share_pct": 23.0
    }
  ],
  "segments": { ... },
  "top_companies": [ ... ]
}
```

### 2. Chip Forecast
```bash
python cli.py chip-forecast [horizon]
```
**Parameters:**
- `horizon`: monthly, quarterly, yearly (default: yearly)

**Examples:**
```bash
python cli.py chip-forecast yearly
```

**Output:**
```json
{
  "current_year": {
    "year": 2023,
    "total_market_bn": 527.0,
    "yoy_growth_pct": -8.2
  },
  "forecasts": [
    {
      "year": 2024,
      "total_market_bn": 576.0,
      "yoy_growth_pct": 9.3,
      "drivers": ["AI chip demand", "Inventory recovery"]
    },
    {
      "year": 2025,
      "total_market_bn": 630.0,
      "yoy_growth_pct": 9.4
    }
  ],
  "segment_forecasts": {
    "memory": {
      "2024_growth_pct": 12.0,
      "outlook": "Strong recovery from 2023 downturn, HBM demand from AI"
    }
  },
  "regional_forecasts": { ... }
}
```

### 3. Fab Utilization
```bash
python cli.py fab-util [granularity]
```
**Parameters:**
- `granularity`: industry, regional, company (default: industry)

**Examples:**
```bash
python cli.py fab-util industry
python cli.py fab-util regional
python cli.py fab-util company
```

**Output (company granularity):**
```json
{
  "benchmarks": {
    "healthy_min_pct": 80.0,
    "optimal_pct": 85.0,
    "current_estimate_pct": 77.0
  },
  "current": {
    "industry_avg_pct": 77.0,
    "status": "Below optimal",
    "interpretation": "Excess capacity during inventory correction"
  },
  "company_utilization": {
    "TSMC": {
      "overall_pct": 85.0,
      "advanced_nodes_pct": 92.0,
      "mature_nodes_pct": 78.0,
      "outlook": "Strong bookings through 2024, AI driving advanced nodes"
    },
    "Samsung": {
      "overall_pct": 70.0,
      "memory_pct": 65.0,
      "foundry_pct": 75.0,
      "outlook": "Memory recovery expected H2 2024"
    }
  },
  "supply_demand": {
    "current_balance": "Slight oversupply in mature nodes, tight in advanced nodes",
    "lead_times_weeks": {
      "advanced_logic": 16,
      "memory": 12,
      "analog": 20
    }
  }
}
```

### 4. Chip Summary
```bash
python cli.py chip-summary
```
Comprehensive market overview combining all data sources.

**Output:**
```json
{
  "market_overview": { ... },
  "regional_markets": { ... },
  "segments": { ... },
  "top_companies": [ ... ],
  "fab_utilization": { ... },
  "key_trends": [
    {
      "trend": "AI Boom",
      "impact": "Driving demand for advanced logic (GPUs, AI accelerators), HBM memory",
      "winners": ["Nvidia", "TSMC", "SK Hynix"]
    },
    {
      "trend": "Geopolitical Fragmentation",
      "impact": "US-China tensions driving fab localization, export controls",
      "implications": ["CHIPS Act", "China domestic push", "Friend-shoring"]
    }
  ]
}
```

## MCP Tools

### 1. `get_semiconductor_sales`
Get monthly semiconductor chip sales by region (SIA data).

**Parameters:**
- `region` (string, optional): all, americas, europe, japan, asia_pacific (default: all)
- `months` (integer, optional): Number of months (default: 12)

**Example:**
```json
{
  "tool": "get_semiconductor_sales",
  "arguments": {
    "region": "americas",
    "months": 6
  }
}
```

### 2. `get_chip_forecast`
Get WSTS semiconductor market forecasts by segment and region.

**Parameters:**
- `horizon` (string, optional): monthly, quarterly, yearly (default: yearly)

**Example:**
```json
{
  "tool": "get_chip_forecast",
  "arguments": {
    "horizon": "yearly"
  }
}
```

### 3. `get_fab_utilization`
Get semiconductor fab utilization rates by region and company.

**Parameters:**
- `granularity` (string, optional): industry, regional, company (default: industry)

**Example:**
```json
{
  "tool": "get_fab_utilization",
  "arguments": {
    "granularity": "company"
  }
}
```

### 4. `get_chip_market_summary`
Get comprehensive semiconductor market summary with trends and forecasts.

**Parameters:** None

**Example:**
```json
{
  "tool": "get_chip_market_summary",
  "arguments": {}
}
```

## Key Market Trends (2024-2025)

### 1. AI Boom 🚀
- **Impact**: Driving demand for advanced logic (GPUs, AI accelerators), HBM memory
- **Winners**: Nvidia, TSMC, SK Hynix
- **Growth**: Advanced node utilization at 92%+ at TSMC

### 2. Inventory Correction Recovery 📉→📈
- **Timeline**: Bottom reached Q1 2024
- **2023**: -8.2% YoY decline due to destocking
- **2024 Forecast**: +9.3% recovery driven by AI and auto

### 3. Geopolitical Fragmentation 🌐
- **US-China Tensions**: Export controls on advanced chips
- **CHIPS Act**: $52B US government investment in domestic fabs
- **Friend-shoring**: Supply chain diversification to allied nations

### 4. Advanced Packaging Revolution 📦
- **Key Technologies**: CoWoS, HBM (High Bandwidth Memory), UCIe (chiplet interconnect)
- **Drivers**: AI/HPC performance requirements
- **Leaders**: TSMC, Intel, Samsung

### 5. Auto Recovery & EV Growth 🚗
- **Status**: Chip shortages easing
- **Growth Segments**: Power discrete, MCUs, Sensors
- **Outlook**: Long-term structural demand from EV adoption

## Market Forecast Summary

### 2024 Outlook (+9.3% YoY)
- **Total Market**: $576B
- **Strongest Segments**: Memory (+12%), Logic (+11%)
- **Regional Leaders**: Americas (+10%), Asia-Pacific (+10%)
- **Key Drivers**: AI acceleration, inventory recovery, auto strength

### 2025 Outlook (+9.4% YoY)
- **Total Market**: $630B
- **Emerging Drivers**: 5G expansion, Edge computing, IoT, EV adoption
- **Structural Growth**: Advanced packaging, chiplets, heterogeneous integration

## Supply/Demand Indicators

### Current Balance
- **Advanced Nodes**: Tight supply, 16-week lead times
- **Mature Nodes**: Slight oversupply, 20-24 week lead times for analog/power

### Pricing Pressure
- **Memory**: Recovering from 2023 lows, HBM premiums
- **Logic**: Stable, premium pricing for leading edge (3nm, 4nm)
- **Analog/Power**: Firm pricing, persistent capacity constraints

## Investment Implications

### Bullish Signals
- Fab utilization rising from 75% (2023) toward 80%+
- AI driving structural demand for advanced nodes
- WSTS multi-year growth outlook (+9-10% annually)
- CHIPS Act reducing geopolitical risk

### Risks to Monitor
- Cyclical demand volatility (memory especially)
- US-China tensions and export controls
- Overcapacity in mature nodes
- Inventory correction recurrence risk

## Data Quality

### Strengths
- FRED provides reliable macro proxies (production indices)
- WSTS forecasts are industry standard
- Company earnings calls offer real-time utilization updates

### Limitations
- SIA detailed monthly data requires subscription (using FRED proxies)
- Fab utilization estimates based on public disclosures
- Some regional data interpolated from market share estimates

## Next Steps (Future Enhancements)

1. **Real-time Scraping**: Automate SIA monthly report scraping
2. **Equipment Tracking**: Add SEMI billings data (capex proxy)
3. **Trade Flow Analysis**: Integrate Census Bureau semiconductor trade data
4. **Stock Correlations**: Link chip sales to SOX index constituents
5. **Predictive Models**: Build leading indicators from equipment orders

## References

### Data Sources
- FRED: https://fred.stlouisfed.org/series/IPB53122S
- WSTS: https://www.wsts.org/
- SIA: https://www.semiconductors.org/
- Company Earnings: TSMC, Samsung, Intel investor relations

### Industry Reports
- TSMC Technology Symposium 2023
- Samsung Electronics Q4 2023 Earnings
- Intel Investor Day 2023
- SEMI Industry Reports

---
**Phase 195 Status**: ✅ DONE  
**LOC**: 506  
**Build Date**: February 25, 2026  
**Author**: QUANTCLAW DATA Build Agent
