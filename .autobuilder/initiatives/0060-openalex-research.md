# 0060 — OpenAlex Scholarly Research API

## What
Build `openalex_research.py` module for OpenAlex — a free, open catalog of 250M+ scholarly works, 100K+ journals, and 100M+ authors. OpenAlex tracks research publications, citations, institutional affiliations, and topic trends across all scientific disciplines. This is alternative data for tracking corporate R&D output, pharma pipeline signals, technology trend detection, and university-industry knowledge transfer.

## Why
Research publication velocity is a leading indicator for innovation-driven sectors. Pharma companies publish clinical research 6-18 months before FDA decisions — tracking publication surges by company/drug target predicts pipeline outcomes. Semiconductor firms file research papers on next-gen architectures years before products ship. University-industry co-authorship reveals technology transfer deals before they're announced. Citation velocity identifies breakthrough research that drives future patents and M&A. OpenAlex replaced Microsoft Academic Graph and is now the largest free scholarly data source available.

## API
- Base: `https://api.openalex.org`
- Protocol: REST
- Auth: None (polite pool: add `mailto:` in User-Agent for faster rate limits)
- Formats: JSON
- Rate limits: 10 req/sec (anonymous), 100 req/sec (with email in User-Agent)
- Docs: https://docs.openalex.org/

## Key Endpoints
- `GET /works?filter=publication_year:2026,authorships.institutions.ror:https://ror.org/{ror_id}&sort=cited_by_count:desc` — Top-cited works by institution
- `GET /works?filter=default.search:{keyword},publication_year:2025-2026&group_by=publication_year` — Publication count trend by keyword
- `GET /works?filter=authorships.institutions.lineage:I136199984,publication_year:2026` — Works by institution (e.g., Harvard)
- `GET /institutions/{openalex_id}?select=display_name,works_count,cited_by_count,summary_stats` — Institution research profile
- `GET /topics?filter=works_count:>1000&sort=works_count:desc` — Top research topics by volume
- `GET /works?filter=concepts.id:C71924100,publication_year:2026&group_by=authorships.institutions.id` — Works by concept (e.g., "Machine Learning") grouped by institution

## Key Indicators & Use Cases
- **Corporate R&D Output** — Publication count by company-affiliated institution (Pfizer, Novartis, Google, NVIDIA)
- **Drug Target Research Velocity** — Publication surge on specific drug targets (GLP-1, KRAS, PD-L1) as pipeline signal
- **Technology Trend Detection** — Emerging topic identification (quantum computing, solid-state batteries, gene editing)
- **Citation Impact Scores** — Highly-cited paper detection for breakthrough identification
- **University-Industry Collaboration** — Co-authorship patterns between pharma/tech companies and universities
- **Country Innovation Index** — Research output per capita by country, useful for EM growth models
- **Sector R&D Intensity** — Publication trends by sector (biotech, semiconductors, energy, AI)

## Pre-configured Company ROR IDs
- **Pfizer:** `https://ror.org/01xdqrp08`
- **Novartis:** `https://ror.org/02f9zrr09`
- **Roche:** `https://ror.org/00by1q217`
- **Google/Alphabet:** `https://ror.org/00njsd438` (Google Research)
- **Microsoft:** `https://ror.org/00d0nc645` (Microsoft Research)
- **NVIDIA:** `https://ror.org/03fhm3131`
- **Samsung:** `https://ror.org/03wnk9277` (Samsung Research)
- **TSMC:** `https://ror.org/02s1m8p66`

## Module
- Filename: `openalex_research.py`
- Cache: 24h (publication data updates daily)
- Auth: None required (polite pool with email recommended)

## Test Commands
```bash
python modules/openalex_research.py                                    # Research trend summary
python modules/openalex_research.py institution pfizer                 # Pfizer R&D output
python modules/openalex_research.py topic "GLP-1 receptor agonist"     # Drug target research trend
python modules/openalex_research.py topic "solid state battery"        # Tech trend detection
python modules/openalex_research.py trending                           # Fastest-growing research topics
python modules/openalex_research.py company_compare pfizer novartis    # Head-to-head R&D comparison
python modules/openalex_research.py country_innovation                 # Country-level output rankings
```

## Acceptance
- [ ] Fetches publication counts and citation metrics by institution/topic/keyword
- [ ] Returns structured JSON: work_id, title, publication_date, cited_by_count, institution, topic, source
- [ ] Institution research profile queries (by ROR ID or name search)
- [ ] Topic/keyword publication trend time series (yearly/monthly)
- [ ] Pre-configured major pharma/tech company ROR IDs for quick lookup
- [ ] Trending topic detection (fastest-growing research areas)
- [ ] 24h caching
- [ ] CLI: `python openalex_research.py [command] [args]`
- [ ] No API key required (polite pool email in User-Agent)
- [ ] Cursor pagination for large result sets (per_page + cursor)
- [ ] Handles OpenAlex entity resolution (institutions, concepts, topics)
- [ ] Group-by aggregation support for time series construction
