# 0036 — ECB Enhanced (Monetary Aggregates + Surveys)

## What
Enhance existing `ecb.py` with broader coverage.

## New Series to Add
- M1, M2, M3 monetary aggregates (BSI dataflow)
- Bank lending survey results (BLS)
- SAFE survey (SME access to finance)
- Composite cost of borrowing
- Securities holdings statistics
- TARGET payment volumes
- Supervisory banking statistics (CBD)

## Acceptance
- [ ] Adds 10+ new series to ECB module
- [ ] Monetary aggregate fetching works
- [ ] Survey data accessible
- [ ] No breaking changes to existing indicators
- [ ] CLI testable with new series keys
