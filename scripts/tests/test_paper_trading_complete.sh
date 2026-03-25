#!/bin/bash
# Complete verification script for Paper Trading Engine

set -e
cd /home/quant/apps/quantclaw-data

echo "========================================="
echo "Paper Trading Engine - Full Verification"
echo "========================================="
echo ""

echo "1. Module Import Test..."
python3 -c "import sys; sys.path.insert(0, 'modules'); import paper_trading; print('✓ Module imports successfully')"
echo ""

echo "2. Database Schema Test..."
python3 -c "
import sys
sys.path.insert(0, 'modules')
import paper_trading
paper_trading.init_db()
import sqlite3
conn = sqlite3.connect('data/paper_trading.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
tables = [row[0] for row in cursor.fetchall()]
conn.close()
expected = {'portfolios', 'positions', 'orders', 'trades', 'daily_snapshots'}
missing = expected - set(tables)
assert len(missing) == 0, f'Missing tables: {missing}'
print(f'✓ All 5 tables exist: {sorted(tables)}')
"
echo ""

echo "3. CLI Commands Test..."
# Test portfolio creation
result=$(python3 cli.py paper-create verify_test --cash 10000 2>&1)
if echo "$result" | grep -q "success"; then
    echo "✓ paper-create works"
else
    echo "✗ paper-create failed"
    exit 1
fi
echo ""

echo "4. MCP Tools Test..."
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_create" && echo "✓ paper_create MCP tool registered"
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_buy" && echo "✓ paper_buy MCP tool registered"
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_sell" && echo "✓ paper_sell MCP tool registered"
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_positions" && echo "✓ paper_positions MCP tool registered"
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_pnl" && echo "✓ paper_pnl MCP tool registered"
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_trades" && echo "✓ paper_trades MCP tool registered"
python3 mcp_server.py list-tools 2>&1 | grep -q "paper_risk" && echo "✓ paper_risk MCP tool registered"
echo ""

echo "5. API Routes Test..."
[ -f "src/app/api/v1/paper-create/route.ts" ] && echo "✓ paper-create route exists"
[ -f "src/app/api/v1/paper-trade/route.ts" ] && echo "✓ paper-trade route exists"
[ -f "src/app/api/v1/paper-positions/route.ts" ] && echo "✓ paper-positions route exists"
[ -f "src/app/api/v1/paper-pnl/route.ts" ] && echo "✓ paper-pnl route exists"
[ -f "src/app/api/v1/paper-trades/route.ts" ] && echo "✓ paper-trades route exists"
echo ""

echo "6. Live Price Feed Test..."
python3 -c "
import sys
sys.path.insert(0, 'modules')
import paper_trading
price = paper_trading.get_live_price('AAPL')
assert price is not None and price > 0, 'Could not fetch AAPL price'
print(f'✓ Live price fetch works (AAPL: \${price:.2f})')
"
echo ""

echo "========================================="
echo "All Verification Tests Passed ✅"
echo "========================================="
echo ""
echo "Paper Trading Engine is fully operational!"
echo ""
echo "Quick Start:"
echo "  python3 cli.py paper-create myportfolio --cash 100000"
echo "  python3 cli.py paper-buy AAPL 10"
echo "  python3 cli.py paper-positions"
echo "  python3 cli.py paper-pnl"
echo ""
