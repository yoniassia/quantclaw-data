#!/usr/bin/env python3
"""Test OpenBB Platform module"""
import json
import sys
sys.path.insert(0, 'modules')
from openbb_platform import *

test_results = {}

print("=== Testing OpenBB Platform Module ===\n")

# Test 1: Stock Quote
print("1. Testing get_stock_quote(AAPL)...")
try:
    result = get_stock_quote('AAPL')
    if 'error' in result:
        print(f"   FAIL: {result['error']}")
        test_results['get_stock_quote'] = 'F'
    elif 'last_price' in result:
        print(f"   PASS: Got quote with price ${result['last_price']}")
        test_results['get_stock_quote'] = 'A'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_stock_quote'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_stock_quote'] = 'F'

# Test 2: Historical Prices
print("\n2. Testing get_historical_prices(MSFT, last 5 days)...")
try:
    result = get_historical_prices('MSFT', '2024-01-01', '2024-01-05')
    if isinstance(result, list) and len(result) > 0 and 'close' in result[0]:
        print(f"   PASS: Got {len(result)} data points")
        test_results['get_historical_prices'] = 'A'
    elif isinstance(result, list) and 'error' in result[0]:
        print(f"   FAIL: {result[0]['error']}")
        test_results['get_historical_prices'] = 'F'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_historical_prices'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_historical_prices'] = 'F'

# Test 3: Financial Statements
print("\n3. Testing get_financial_statements(AAPL)...")
try:
    result = get_financial_statements('AAPL', 'annual')
    if 'error' in result:
        print(f"   FAIL: {result['error']}")
        test_results['get_financial_statements'] = 'F'
    elif 'income_statement' in result and isinstance(result['income_statement'], list):
        print(f"   PASS: Got financial statements")
        test_results['get_financial_statements'] = 'A'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_financial_statements'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_financial_statements'] = 'F'

# Test 4: Analyst Estimates
print("\n4. Testing get_analyst_estimates(AAPL)...")
try:
    result = get_analyst_estimates('AAPL')
    if 'error' in result:
        print(f"   FAIL: {result['error']}")
        test_results['get_analyst_estimates'] = 'F'
    elif 'consensus' in result or 'price_target' in result:
        print(f"   PASS: Got analyst estimates")
        test_results['get_analyst_estimates'] = 'A'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_analyst_estimates'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_analyst_estimates'] = 'F'

# Test 5: Economic Calendar
print("\n5. Testing get_economic_calendar()...")
try:
    result = get_economic_calendar('2024-03-01', '2024-03-07')
    if isinstance(result, list) and len(result) > 0 and not 'error' in result[0]:
        print(f"   PASS: Got {len(result)} events")
        test_results['get_economic_calendar'] = 'A'
    elif isinstance(result, list) and len(result) > 0 and 'error' in result[0]:
        print(f"   FAIL: {result[0]['error']}")
        test_results['get_economic_calendar'] = 'F'
    else:
        print(f"   PARTIAL: No events or {result}")
        test_results['get_economic_calendar'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_economic_calendar'] = 'F'

# Test 6: ETF Holdings
print("\n6. Testing get_etf_holdings(SPY)...")
try:
    result = get_etf_holdings('SPY')
    if isinstance(result, list) and len(result) > 0 and not 'error' in result[0]:
        print(f"   PASS: Got {len(result)} holdings")
        test_results['get_etf_holdings'] = 'A'
    elif isinstance(result, list) and 'error' in result[0]:
        print(f"   FAIL: {result[0]['error']}")
        test_results['get_etf_holdings'] = 'F'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_etf_holdings'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_etf_holdings'] = 'F'

# Test 7: Options Chains
print("\n7. Testing get_options_chains(AAPL)...")
try:
    result = get_options_chains('AAPL')
    if 'error' in result:
        print(f"   FAIL: {result['error']}")
        test_results['get_options_chains'] = 'F'
    elif 'calls' in result or 'puts' in result:
        print(f"   PASS: Got options chain")
        test_results['get_options_chains'] = 'A'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_options_chains'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_options_chains'] = 'F'

# Test 8: Insider Trading
print("\n8. Testing get_insider_trading(MSFT)...")
try:
    result = get_insider_trading('MSFT', limit=10)
    if isinstance(result, list) and len(result) > 0 and not 'error' in result[0]:
        print(f"   PASS: Got {len(result)} insider transactions")
        test_results['get_insider_trading'] = 'A'
    elif isinstance(result, list) and 'error' in result[0]:
        print(f"   FAIL: {result[0]['error']}")
        test_results['get_insider_trading'] = 'F'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_insider_trading'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_insider_trading'] = 'F'

# Test 9: Institutional Holders
print("\n9. Testing get_institutional_holders(AAPL)...")
try:
    result = get_institutional_holders('AAPL')
    if isinstance(result, list) and len(result) > 0 and not 'error' in result[0]:
        print(f"   PASS: Got {len(result)} institutional holders")
        test_results['get_institutional_holders'] = 'A'
    elif isinstance(result, list) and 'error' in result[0]:
        print(f"   FAIL: {result[0]['error']}")
        test_results['get_institutional_holders'] = 'F'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_institutional_holders'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_institutional_holders'] = 'F'

# Test 10: News
print("\n10. Testing get_news(SPY)...")
try:
    result = get_news('SPY', limit=5)
    if isinstance(result, list) and len(result) > 0 and 'title' in result[0]:
        print(f"   PASS: Got {len(result)} news articles")
        test_results['get_news'] = 'A'
    elif isinstance(result, list) and 'error' in result[0]:
        print(f"   FAIL: {result[0]['error']}")
        test_results['get_news'] = 'F'
    else:
        print(f"   PARTIAL: {result}")
        test_results['get_news'] = 'C'
except Exception as e:
    print(f"   FAIL: {e}")
    test_results['get_news'] = 'F'

# Summary
print("\n=== Test Summary ===")
print(json.dumps(test_results, indent=2))

# Calculate grade
grades = list(test_results.values())
a_count = grades.count('A')
c_count = grades.count('C')
f_count = grades.count('F')

if f_count == 0 and c_count == 0:
    overall = 'A'
elif f_count <= 2:
    overall = 'B'
elif f_count <= 5:
    overall = 'C'
else:
    overall = 'F'

print(f"\nOverall Grade: {overall}")
print(f"Breakdown: {a_count} passing, {c_count} partial, {f_count} failing")
