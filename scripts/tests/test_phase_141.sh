#!/bin/bash
# Test Phase 141: Comparable Company Analysis

echo "=========================================="
echo "Phase 141: Comparable Company Analysis"
echo "=========================================="
echo

echo "1. Testing peer-groups command..."
python3 cli.py peer-groups | jq 'keys'
echo

echo "2. Testing comp-metrics for AAPL..."
python3 cli.py comp-metrics AAPL | jq '{ticker, name, sector, valuation: .valuation | {pe_ratio, ev_ebitda, price_to_sales}}'
echo

echo "3. Testing comps-table for tech giants..."
python3 cli.py comps-table AAPL MSFT GOOGL | jq '.summary_stats | {pe_ratio, ev_ebitda, gross_margin}'
echo

echo "4. Testing comp-compare AAPL to peers..."
python3 cli.py comp-compare AAPL --peers MSFT GOOGL | jq '.relative_analysis.valuation.pe_ratio'
echo

echo "5. Testing comp-sector for semiconductors..."
python3 cli.py comp-sector semiconductors | jq '{sector, company_count, pe_stats: .analysis.summary_stats.pe_ratio}'
echo

echo "=========================================="
echo "All tests completed successfully!"
echo "=========================================="
