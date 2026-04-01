# 0023 — EDINET Japan (Securities Filings API)

## What
Build `edinet_japan.py` for Japan's securities disclosure system.

## API
- Base: `https://disclosure.edinet-fsa.go.jp/api/v2`
- Protocol: REST
- Auth: API key (free registration)
- Formats: JSON (metadata), ZIP (XBRL/CSV documents)
- Store key in `.env` as `EDINET_API_KEY`

## Key Datasets
- Annual securities reports (有価証券報告書)
- Quarterly reports
- Large shareholding reports
- Tender offer reports
- Document listing by date

## Acceptance
- [ ] Document listing by date range
- [ ] Download and parse XBRL/CSV
- [ ] Company search
- [ ] Graceful fallback when no key
- [ ] 24h cache, CLI testable
