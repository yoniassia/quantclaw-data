#!/bin/bash
# Test script for Phase 153: Global Equity Index Returns

echo "=== Phase 153: Global Equity Index Returns Test ==="
echo ""

echo "1. List available indices (Americas region)"
python3 cli.py list --region Americas | jq '.regions.Americas[0:3]'
echo ""

echo "2. Get daily returns for major indices"
python3 modules/global_equity_index_returns.py daily-returns --indices "S&P 500,Nikkei 225,FTSE 100" | jq '.indices[] | {index: .index_name, return: .daily_return, ytd: .ytd_return}'
echo ""

echo "3. Get performance metrics for US indices"
python3 modules/global_equity_index_returns.py performance --indices "S&P 500,Nasdaq Composite,Dow Jones" --days 90 | jq '.performance[] | {index: .index_name, ytd: .ytd_return, volatility: .volatility_30d, sharpe: .sharpe_ratio}'
echo ""

echo "4. Regional performance (Asia-Pacific)"
python3 cli.py regional --region "Asia-Pacific" | jq '.regions[] | {region, avg_ytd: .average_ytd_return, best: .best_performer}'
echo ""

echo "5. Compare indices on YTD return"
python3 cli.py compare --indices "S&P 500,FTSE 100,DAX,Nikkei 225" --metric ytd_return | jq '.comparison[0:3]'
echo ""

echo "6. List all regions"
python3 cli.py list | jq '.regions | keys'
echo ""

echo "=== All Phase 153 Tests Complete ==="
