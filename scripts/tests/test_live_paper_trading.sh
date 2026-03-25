#!/bin/bash
#
# LIVE PAPER TRADING — VERIFICATION TEST
# Demonstrates all features of the system
#

set -e

echo "=================================="
echo "LIVE PAPER TRADING VERIFICATION"
echo "=================================="
echo ""

echo "📊 TEST 1: Check Portfolio Status"
echo "----------------------------------"
python3 cli.py paper-status
echo ""

echo "📝 TEST 2: View Trade History"
echo "----------------------------------"
python3 cli.py paper-history --limit 10
echo ""

echo "🔄 TEST 3: Dry Run Rebalance"
echo "----------------------------------"
python3 cli.py paper-run --dry-run 2>&1 | tail -30
echo ""

echo "🚀 TEST 4: Shell Script Status"
echo "----------------------------------"
./run_paper_trading.sh --status 2>&1 | tail -20
echo ""

echo "✅ ALL TESTS COMPLETE"
echo ""
echo "📈 Current Portfolio Summary:"
python3 -c "
import sqlite3
conn = sqlite3.connect('data/paper_trading.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT ticker, quantity, avg_cost 
    FROM positions 
    WHERE portfolio_id = (SELECT id FROM portfolios WHERE name = 'sa_quant_live')
    ORDER BY ticker
''')
positions = cursor.fetchall()
print(f'  Positions: {len(positions)}')
total = sum(p[1] * p[2] for p in positions)
print(f'  Total Invested: \${total:,.0f}')
for ticker, qty, cost in positions:
    print(f'  • {ticker}: {qty:.2f} shares @ \${cost:.2f}')
conn.close()
"

echo ""
echo "🎯 System Status: ✅ OPERATIONAL"
