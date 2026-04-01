# 0042 — EU Small Statistics Offices Batch

## What
Build `eu_small_statistics.py` — unified module for smaller EU stats offices.

## Countries Covered
- Bulgaria (NSI) — nsi.bg
- Croatia (DZS) — dzs.hr
- Cyprus (CYSTAT) — cystat.gov.cy
- Greece (ELSTAT) — statistics.gr
- Hungary (KSH) — ksh.hu
- Latvia (CSB) — csb.gov.lv
- Lithuania (Statistics Lithuania) — stat.gov.lt
- Luxembourg (STATEC) — statec.lu
- Malta (NSO) — nso.gov.mt
- Romania (INS) — insse.ro
- Slovakia (SO SR) — statistics.sk
- Slovenia (SURS) — stat.si

## Pattern
Unified module. For most: prefer Eurostat SDMX with country filter over direct national sources.
National source only when Eurostat doesn't have the granularity.

## Key Datasets
- GDP, CPI, unemployment for each country (via Eurostat filter)
- National-specific indicators where available

## Acceptance
- [ ] GDP, CPI, unemployment for all 12 countries
- [ ] Uses Eurostat SDMX as primary, national as fallback
- [ ] 24h cache
- [ ] CLI: `python eu_small_statistics.py [country] [indicator]`
