# 0046 — USPTO PatentsView API

## What
Build `patentsview_uspto.py` module for querying U.S. patent grants and applications data. PatentsView provides structured, queryable access to all USPTO patent data — invaluable alternative data for tracking corporate innovation pipelines, technology trends, and R&D intensity by sector.

## Why
Patent filings are a leading indicator for pharma pipelines, semiconductor roadmaps, and tech M&A targets. Tracking patent velocity by assignee or CPC class gives quant signals months before earnings reflect R&D output.

## API
- Base: `https://search.patentsview.org/api/v1`
- Protocol: REST (POST queries, GET by ID)
- Auth: None (fully open, no key required)
- Formats: JSON
- Rate limits: 45 requests/minute
- Docs: https://patentsview.org/apis/api-endpoints

## Key Endpoints
- `POST /patents/` — Search patent grants with filters (assignee, date, CPC class, keyword)
- `POST /patent_applications/` — Search pending applications
- `POST /assignees/` — Company/institution patent portfolios
- `GET /patents/{patent_id}` — Single patent detail
- `POST /cpc_subgroups/` — Technology classification lookup

## Indicators to Implement
- Patent grant count by assignee (company) over time
- Patent application velocity (filings per quarter by company/sector)
- Top assignees by CPC class (e.g., H01L for semiconductors, A61K for pharma)
- Citation network metrics (forward citations as quality proxy)
- Technology hotspot detection (fastest-growing CPC classes)
- Cross-assignee collaboration (co-assigned patents)

## Module
- Filename: `patentsview_uspto.py`
- Cache: 24h (patent data is static once published)

## Test Commands
```bash
python modules/patentsview_uspto.py                          # Latest patent grants
python modules/patentsview_uspto.py patent_grants_by_assignee AAPL
python modules/patentsview_uspto.py tech_trends H01L         # Semiconductor patents
python modules/patentsview_uspto.py top_assignees             # Most active filers
```

## Acceptance
- [ ] Queries patent grants with date range, assignee, CPC filters
- [ ] Returns structured JSON: patent_id, title, assignee, date, cpc_class, citation_count
- [ ] Assignee portfolio lookup (by name or ticker mapping)
- [ ] CPC class trend aggregation
- [ ] 24h caching
- [ ] CLI: `python patentsview_uspto.py [command] [args]`
- [ ] Handles rate limiting (45 req/min) with backoff
