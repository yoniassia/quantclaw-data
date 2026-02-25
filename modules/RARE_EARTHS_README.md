# Rare Earths & Strategic Minerals Module

## Overview

Phase 178 of the QuantClaw Data project provides comprehensive analysis of strategic minerals, rare earth elements, and supply chain risk assessment based on USGS Mineral Commodity Summaries data.

## Features

- **Mineral Profiles**: Production, reserves, uses, and supply concentration for 7 critical minerals
- **Supply Risk Assessment**: Multi-factor risk scoring with geopolitical analysis
- **Sector Exposure Analysis**: Defense, energy, electronics, aerospace, and medical sector dependency
- **Country Production Profiles**: Track major producers and market shares
- **Rare Earths Deep Dive**: 17 rare earth elements with detailed market dynamics

## Data Sources

All data derived from **USGS Mineral Commodity Summaries** (public domain):
- Global production by country (metric tons)
- Reserves and resources
- US import reliance percentages
- Primary use cases and applications

**No API key required**. Data updated monthly based on USGS publications.

## Tracked Minerals

### Available Minerals (7)
1. **Rare Earths** - 17 elements critical for magnets, catalysts, electronics
2. **Lithium** - Battery technology, EVs, energy storage
3. **Cobalt** - Batteries, superalloys, industrial catalysts
4. **Graphite** - Battery anodes, lubricants, steel production
5. **Tungsten** - Cemented carbides, defense applications
6. **Gallium** - Integrated circuits, optoelectronics, solar
7. **Germanium** - Fiber optics, infrared optics, catalysts

### Critical Minerals List (35)
Aluminum, Antimony, Arsenic, Barite, Beryllium, Bismuth, Cesium, Chromium, Cobalt, Fluorspar, Gallium, Germanium, Graphite, Hafnium, Helium, Indium, Lithium, Magnesium, Manganese, Niobium, Platinum Group, Potash, Rare Earths, Rubidium, Scandium, Strontium, Tantalum, Tellurium, Tin, Titanium, Tungsten, Uranium, Vanadium, Zinc, Zirconium

## CLI Commands

```bash
# List available minerals and sectors
python cli.py list-minerals
python cli.py list-sectors

# Get mineral profile with production data
python cli.py mineral-profile rare_earths
python cli.py mineral-profile lithium

# Calculate supply chain risk score
python cli.py supply-risk cobalt
python cli.py supply-risk graphite

# Rank all minerals by risk
python cli.py risk-rankings

# Analyze sector exposure to supply disruptions
python cli.py sector-exposure defense
python cli.py sector-exposure energy
python cli.py sector-exposure electronics

# Get country production profile
python cli.py country-profile china
python cli.py country-profile united_states

# Detailed rare earth elements analysis
python cli.py rare-earths-detailed

# Comprehensive strategic minerals report
python cli.py comprehensive-report
```

## MCP Tools

All commands exposed via Model Context Protocol:

- `mineral_profile` - Comprehensive mineral data
- `supply_risk_score` - Multi-factor risk assessment
- `supply_risk_rankings` - All minerals ranked by risk
- `sector_exposure` - Sector dependency analysis
- `country_production_profile` - Country-level production data
- `rare_earths_detailed` - Deep dive on rare earth elements
- `minerals_comprehensive_report` - Full strategic minerals report
- `list_critical_minerals` - List tracked minerals

## Supply Risk Methodology

**4-Factor Risk Score (0-100)**:

1. **Import Reliance (25%)** - US import dependence percentage
2. **Supply Concentration (30%)** - Herfindahl-Hirschman Index (HHI) of producer concentration
3. **Producer Dominance (20%)** - Top producer market share
4. **Geopolitical Risk (25%)** - China production share

**Risk Ratings**:
- **CRITICAL**: Score ≥ 75 (Gallium, Germanium)
- **HIGH**: Score ≥ 60 (Graphite, Tungsten, Rare Earths)
- **MODERATE**: Score ≥ 40 (Cobalt)
- **LOW**: Score < 40 (Lithium)

## Herfindahl-Hirschman Index (HHI)

Market concentration measured by sum of squared market shares:
- **HHI > 2500**: HIGH concentration risk
- **HHI 1500-2500**: MODERATE concentration risk
- **HHI < 1500**: LOW concentration risk

## Example Outputs

### Mineral Profile
```json
{
  "mineral": "rare_earths",
  "global_production_mt": 300000,
  "top_producers": {
    "china": {"production_mt": 210000, "share_pct": 70.0}
  },
  "supply_concentration": {
    "hhi": 5223.47,
    "risk_level": "HIGH"
  },
  "us_import_reliance_pct": 74,
  "strategic_sectors": ["defense", "energy", "electronics"]
}
```

### Supply Risk Rankings
```json
[
  {"mineral": "gallium", "risk_score": 90.46, "risk_rating": "CRITICAL"},
  {"mineral": "germanium", "risk_score": 79.72, "risk_rating": "CRITICAL"},
  {"mineral": "graphite", "risk_score": 70.68, "risk_rating": "HIGH"}
]
```

### Sector Exposure
```json
{
  "sector": "defense",
  "sector_risk_score": 60.76,
  "sector_risk_rating": "HIGH",
  "mineral_risk_profiles": [
    {"mineral": "tungsten", "risk_score": 69.79},
    {"mineral": "rare_earths", "risk_score": 65.67}
  ]
}
```

## Strategic Sectors

| Sector | Critical Minerals |
|--------|------------------|
| Defense | Tungsten, Cobalt, Rare Earths, Titanium, Beryllium |
| Energy | Lithium, Cobalt, Rare Earths, Graphite, Nickel, Copper |
| Electronics | Rare Earths, Gallium, Germanium, Indium, Tantalum |
| Aerospace | Titanium, Aluminum, Nickel, Rare Earths |
| Medical | Helium, Cobalt, Platinum Group, Rare Earths |

## Rare Earth Elements (17)

**Light REE**: Lanthanum, Cerium, Praseodymium, Neodymium, Promethium, Samarium  
**Heavy REE**: Europium, Gadolinium, Terbium, Dysprosium, Holmium, Erbium, Thulium, Ytterbium, Lutetium  
**Other**: Scandium, Yttrium

### Key Applications
- **Permanent Magnets**: Neodymium, Dysprosium (EV motors, wind turbines)
- **Catalysts**: Lanthanum, Cerium (petroleum refining, automotive)
- **Phosphors**: Europium, Terbium, Yttrium (displays, lighting)
- **Glass Polishing**: Cerium oxide

## China Dominance

| Mineral | China Production Share |
|---------|----------------------|
| Gallium | 90.6% |
| Tungsten | 82.1% |
| Germanium | 79.2% |
| Rare Earths | 70.0% |
| Graphite | 68.5% |

## Use Cases

1. **National Security Analysis**: Identify defense supply chain vulnerabilities
2. **Investment Research**: Track critical mineral producers and projects
3. **Policy Planning**: Inform strategic stockpile and diversification decisions
4. **ESG Screening**: Assess rare earth supply chain risks in portfolios
5. **Energy Transition**: Monitor battery and clean energy mineral dependencies

## Technical Details

- **Lines of Code**: 592
- **Phase**: 178
- **Category**: Commodities
- **Update Frequency**: Monthly (USGS publication cycle)
- **Dependencies**: `requests`, `json`, `datetime`, `typing`

## Future Enhancements

- Real-time pricing data integration (London Metal Exchange, spot markets)
- Mine production capacity tracking
- Recycling and secondary supply analysis
- Trade flow monitoring (UN Comtrade integration)
- Project pipeline and exploration activity
- Technology substitution risk assessment
- Historical price volatility analysis

## References

- [USGS Mineral Commodity Summaries](https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries)
- [Critical Minerals List (2022)](https://www.usgs.gov/news/national-news-release/us-geological-survey-releases-2022-list-critical-minerals)
- Department of Energy Critical Materials Strategy
- World Bank Climate-Smart Mining Initiative

---

**Author**: QUANTCLAW DATA Build Agent  
**Built**: February 2026  
**Status**: Production-ready
