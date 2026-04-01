# 0053 — European Patent Office Open Patent Services (OPS)

## What
Build `epo_ops.py` module for the European Patent Office's Open Patent Services API. OPS provides access to the worldwide patent database (DOCDB) covering 100M+ patent documents from 100+ patent authorities. This complements the existing USPTO PatentsView module (0046) with global patent coverage — essential for tracking multinational corporate innovation beyond the US.

## Why
US PatentsView only covers USPTO filings. Many European and Asian companies file first at their home patent offices or at the EPO. OPS provides global patent family data, European patent grants, and PCT (international) applications. Tracking patent families across jurisdictions reveals true corporate R&D intensity and geographic IP strategy — critical alternative data for pharma, semis, and tech.

## API
- Base: `https://ops.epo.org/3.2/rest-services`
- Protocol: REST
- Auth: OAuth2 client credentials (free registration at https://developers.epo.org/)
- Formats: JSON, XML
- Rate limits: 4 GB/week (free tier), 10 requests/second
- Docs: https://developers.epo.org/ops-v3-2

## Key Endpoints
- `POST /published-data/search` — Full-text and structured patent search
- `GET /published-data/publication/epodoc/{doc_id}/biblio` — Bibliographic data
- `GET /published-data/publication/epodoc/{doc_id}/claims` — Patent claims text
- `GET /family/publication/epodoc/{doc_id}` — Patent family members (same invention, different offices)
- `GET /register/publication/epodoc/{doc_id}/biblio` — EP register status (granted, pending, opposed)
- `GET /number-service/v1.0/{number_type}/{number}` — Number format conversion

## Indicators to Implement
- Patent search by applicant name, IPC/CPC class, keyword, date range
- Patent family mapping (link EP/WO/US/JP/CN filings for same invention)
- EP grant rate by technology sector (approval vs rejection trends)
- Applicant filing velocity (filings per quarter by company)
- Technology hotspot detection (fastest-growing IPC classes at EPO)
- Opposition proceedings tracker (challenged patents as competitive intelligence)

## Module
- Filename: `epo_ops.py`
- Cache: 24h (patent data is static once published)
- Auth: Reads `EPO_CONSUMER_KEY` and `EPO_CONSUMER_SECRET` from `.env`

## Test Commands
```bash
python modules/epo_ops.py                                  # Summary: recent EP grants
python modules/epo_ops.py search "autonomous driving"      # Full-text patent search
python modules/epo_ops.py applicant "Samsung"              # Patents by applicant
python modules/epo_ops.py family EP3456789                 # Patent family members
python modules/epo_ops.py tech_trends H01L                 # Semiconductor filings at EPO
```

## Acceptance
- [ ] OAuth2 token acquisition and refresh from EPO credentials
- [ ] Patent search by keyword, applicant, IPC class, date range
- [ ] Returns structured JSON: doc_id, title, applicant, date, ipc_class, family_id
- [ ] Patent family resolution (cross-office linking)
- [ ] EP register status lookup (granted/pending/opposed)
- [ ] 24h caching
- [ ] CLI: `python epo_ops.py [command] [args]`
- [ ] Handles rate limiting (10 req/s) and weekly quota tracking
