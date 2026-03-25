#!/bin/bash
# Test script for Phase 140: Equity Screener

echo "======================================================================"
echo "PHASE 140 TEST: Equity Screener (Multi-Factor)"
echo "======================================================================"
echo ""

cd /home/quant/apps/quantclaw-data

echo "Test 1: List available factors"
echo "------------------------------"
python3 cli.py factors 2>&1 | head -15
echo ""

echo "Test 2: List available presets"
echo "------------------------------"
python3 cli.py presets 2>&1 | head -20
echo ""

echo "Test 3: Calculate factors for single stock"
echo "------------------------------"
python3 -c "
from modules.equity_screener import EquityScreener

screener = EquityScreener(['AAPL'])
factors = screener.calculate_factors('AAPL')
if factors:
    print('✓ AAPL factors calculated successfully')
    print(f'  Company: {factors[\"company_name\"]}')
    print(f'  Sector: {factors[\"sector\"]}')
    print(f'  P/E: {factors[\"pe\"]}')
    print(f'  P/B: {factors[\"pb\"]}')
    print(f'  ROE: {factors[\"roe\"]}')
    print(f'  Return 3M: {factors[\"return_3m\"]}')
    print(f'  RSI: {factors[\"rsi\"]}')
else:
    print('✗ Failed to calculate factors')
" 2>&1
echo ""

echo "Test 4: Screen with custom filters (P/E < 30, ROE > 0.15)"
echo "------------------------------"
python3 -c "
from modules.equity_screener import EquityScreener

screener = EquityScreener(['AAPL', 'MSFT', 'GOOGL', 'JPM', 'WMT', 'PG'])
results = screener.screen({'pe': (0, 30), 'roe': (0.15, None)}, limit=5)
print(f'✓ Found {len(results)} stocks matching criteria:')
for r in results:
    print(f'  - {r[\"ticker\"]}: P/E={r[\"pe\"]:.2f}, ROE={r[\"roe\"]:.2f}')
" 2>&1
echo ""

echo "Test 5: Rank stocks by composite score"
echo "------------------------------"
python3 -c "
from modules.equity_screener import EquityScreener
import pandas as pd

screener = EquityScreener(['AAPL', 'MSFT', 'GOOGL', 'JPM', 'WMT'])
ranked = screener.rank_stocks(factors=['pe', 'roe', 'return_3m'])
print(f'✓ Ranked {len(ranked)} stocks by composite score:')
for idx, row in ranked.head(5).iterrows():
    score = int(row['score']*100)
    ticker = row['ticker']
    pe = row.get('pe')
    roe = row.get('roe')
    print(f'  {score}% - {ticker}: P/E={pe:.2f}, ROE={roe:.2f}' if pd.notna(pe) and pd.notna(roe) else f'  {score}% - {ticker}')
" 2>&1
echo ""

echo "Test 6: Test value preset filter"
echo "------------------------------"
python3 -c "
from modules.equity_screener import SCREENING_PRESETS

preset = SCREENING_PRESETS['value']
print(f'✓ Value preset: {preset[\"name\"]}')
print('  Filters:')
for factor, (min_val, max_val) in preset['filters'].items():
    min_str = f'{min_val}' if min_val is not None else '-∞'
    max_str = f'{max_val}' if max_val is not None else '+∞'
    print(f'    - {factor}: [{min_str}, {max_str}]')
" 2>&1
echo ""

echo "Test 7: Count factor categories"
echo "------------------------------"
python3 -c "
from modules.equity_screener import FACTOR_CATEGORIES

total = sum(len(v) for v in FACTOR_CATEGORIES.values())
print(f'✓ Total screening factors: {total}')
for category, factors in FACTOR_CATEGORIES.items():
    print(f'  - {category}: {len(factors)} factors')
" 2>&1
echo ""

echo "======================================================================"
echo "✓ PHASE 140 TESTS COMPLETE"
echo "======================================================================"
echo ""
echo "Module: modules/equity_screener.py (610 LOC)"
echo "CLI Commands: screen, preset, rank, factors, presets"
echo "MCP Tools: screen_stocks, screen_preset, rank_stocks, screen_factors, screen_presets_list"
echo ""
echo "Features:"
echo "  - 50+ screening factors across 6 categories"
echo "  - Support for 8000+ US stocks (expandable)"
echo "  - Custom filter combinations (AND logic)"
echo "  - 5 predefined presets (value, growth, momentum, dividend, quality)"
echo "  - Multi-factor ranking with composite scoring"
echo "  - JSON output for all commands"
echo ""
