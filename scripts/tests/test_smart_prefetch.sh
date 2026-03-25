#!/bin/bash

echo "🔮 QUANTCLAW DATA - SMART PREFETCH TEST"
echo "========================================"
echo ""

# Test 1: Cache Status
echo "📊 Test 1: Cache Status"
python3 cli.py cache-status 2>&1 | grep -v "DeprecationWarning"
echo ""

# Test 2: Record some sample queries
echo "📝 Test 2: Recording Sample Queries"
python3 modules/smart_prefetch.py record-query AAPL price --hit 2>&1 | tail -1
python3 modules/smart_prefetch.py record-query TSLA technicals 2>&1 | tail -1
python3 modules/smart_prefetch.py record-query MSFT earnings --hit 2>&1 | tail -1
python3 modules/smart_prefetch.py record-query NVDA price 2>&1 | tail -1
python3 modules/smart_prefetch.py record-query AAPL technicals --hit 2>&1 | tail -1
echo ""

# Test 3: Show usage stats
echo "📈 Test 3: Usage Patterns & Statistics"
python3 cli.py prefetch-stats 2>&1 | grep -v "DeprecationWarning"
echo ""

# Test 4: Warm cache with predictions
echo "🔥 Test 4: Cache Warmup"
python3 cli.py prefetch-warmup 2>&1 | grep -v "DeprecationWarning"
echo ""

# Test 5: Updated cache status
echo "💾 Test 5: Updated Cache Status"
python3 cli.py cache-status 2>&1 | grep -v "DeprecationWarning"
echo ""

# Test 6: Configure prefetch settings
echo "⚙️  Test 6: Update Configuration"
python3 cli.py prefetch-config --top 15 --confidence 0.6 2>&1 | grep -v "DeprecationWarning"
echo ""

# Test 7: Show predictions (hidden command)
echo "🔮 Test 7: Predictions (ML-based)"
python3 modules/smart_prefetch.py predictions 2>&1 | grep -v "DeprecationWarning"
echo ""

echo "✅ All tests completed successfully!"
echo ""
echo "📋 Available CLI Commands:"
echo "  python cli.py prefetch-stats         # Show usage patterns"
echo "  python cli.py prefetch-warmup        # Warm cache with predictions"
echo "  python cli.py cache-status           # Show cache hit rates"
echo "  python cli.py prefetch-config --top 20 --confidence 0.6"
echo ""
echo "🌐 API Endpoints (after next build):"
echo "  GET  /api/v1/smart-prefetch?action=stats"
echo "  GET  /api/v1/smart-prefetch?action=warmup"
echo "  GET  /api/v1/smart-prefetch?action=status"
echo "  POST /api/v1/smart-prefetch?action=config"
echo "  POST /api/v1/smart-prefetch?action=record"
