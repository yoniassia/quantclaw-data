#!/usr/bin/env python3
"""
OpenBB Platform Module

Comprehensive financial data via OpenBB Platform SDK
Aggregates data from multiple providers (Yahoo Finance, FMP, Polygon, etc.)

Functions:
- get_stock_quote(symbol) — Real-time quote
- get_historical_prices(symbol, start, end, interval) — OHLCV data
- get_financial_statements(symbol, period) — Income, balance, cash flow
- get_analyst_estimates(symbol) — Consensus estimates
- get_economic_calendar(start, end) — Macro events
- get_etf_holdings(symbol) — ETF composition
- get_options_chains(symbol) — Options data
- get_insider_trading(symbol) — Insider transactions
- get_institutional_holders(symbol) — 13F holdings
- get_news(symbol) — Financial news

Data Source: OpenBB Platform (openbb.co)
Providers: Yahoo Finance, FMP, Polygon, FRED, and more
Refresh: Real-time to daily depending on data type

Author: QUANTCLAW DATA DevClaw
Phase: OpenBB Integration
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False

# Provider preference (yfinance is free and reliable)
DEFAULT_PROVIDER = "yfinance"


def _format_date(date_obj) -> str:
    """Format date object to YYYY-MM-DD string"""
    if isinstance(date_obj, str):
        return date_obj
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj)


def _handle_result(result, symbol: Optional[str] = None) -> Any:
    """Convert OpenBB result to dict/list"""
    if result is None:
        return {'error': 'No data returned', 'symbol': symbol}
    
    try:
        # Convert to dict
        data = result.to_dict()
        
        # Extract data arrays - OpenBB returns columnar format
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            # Convert columnar to row-based
            keys = list(data.keys())
            if not keys:
                return []
            
            num_rows = len(data[keys[0]])
            rows = []
            for i in range(num_rows):
                row = {k: data[k][i] for k in keys}
                rows.append(row)
            return rows
        
        return data
    except Exception as e:
        return {'error': f'Result conversion failed: {str(e)}', 'symbol': symbol}


def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """
    Get real-time stock quote
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
    
    Returns:
        dict: Current price, volume, bid/ask, 52w high/low, moving averages
    
    Example:
        >>> get_stock_quote('AAPL')
        {'symbol': 'AAPL', 'last_price': 263.55, 'volume': 10143865, ...}
    """
    if not OPENBB_AVAILABLE:
        return {'error': 'OpenBB not installed', 'symbol': symbol}
    
    try:
        result = obb.equity.price.quote(symbol=symbol, provider=DEFAULT_PROVIDER)
        data = _handle_result(result, symbol)
        
        # Return first item if list
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        
        return data if isinstance(data, dict) else {'data': data, 'symbol': symbol}
    
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}


def get_historical_prices(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = '1d'
) -> List[Dict]:
    """
    Get historical OHLCV data
    
    Args:
        symbol: Stock ticker
        start: Start date (YYYY-MM-DD) - defaults to 1 month ago
        end: End date (YYYY-MM-DD) - defaults to today
        interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
    
    Returns:
        list: Historical OHLCV data points
    
    Example:
        >>> get_historical_prices('AAPL', '2024-01-01', '2024-01-31')
        [{'date': '2024-01-02', 'open': 185.0, 'high': 186.0, ...}, ...]
    """
    if not OPENBB_AVAILABLE:
        return [{'error': 'OpenBB not installed', 'symbol': symbol}]
    
    try:
        # Default date range if not provided
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')
        if start is None:
            start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        result = obb.equity.price.historical(
            symbol=symbol,
            start_date=start,
            end_date=end,
            interval=interval,
            provider=DEFAULT_PROVIDER
        )
        
        data = _handle_result(result, symbol)
        return data if isinstance(data, list) else [{'error': 'Invalid format', 'data': data}]
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol}]


def get_financial_statements(symbol: str, period: str = 'annual') -> Dict[str, Any]:
    """
    Get company financial statements
    
    Args:
        symbol: Stock ticker
        period: 'annual', 'quarter', or 'ttm' (trailing twelve months)
    
    Returns:
        dict: Income statement, balance sheet, cash flow statement
    
    Example:
        >>> get_financial_statements('AAPL', 'annual')
        {'income': [...], 'balance': [...], 'cash_flow': [...]}
    """
    if not OPENBB_AVAILABLE:
        return {'error': 'OpenBB not installed', 'symbol': symbol}
    
    try:
        # Map period to OpenBB format
        period_map = {
            'annual': 'annual',
            'quarter': 'quarter',
            'ttm': 'ttm'
        }
        obb_period = period_map.get(period.lower(), 'annual')
        
        # Get all three statements
        income = obb.equity.fundamental.income(
            symbol=symbol,
            period=obb_period,
            limit=5,
            provider=DEFAULT_PROVIDER
        )
        
        balance = obb.equity.fundamental.balance(
            symbol=symbol,
            period=obb_period,
            limit=5,
            provider=DEFAULT_PROVIDER
        )
        
        cash_flow = obb.equity.fundamental.cash(
            symbol=symbol,
            period=obb_period,
            limit=5,
            provider=DEFAULT_PROVIDER
        )
        
        return {
            'symbol': symbol,
            'period': period,
            'income_statement': _handle_result(income, symbol),
            'balance_sheet': _handle_result(balance, symbol),
            'cash_flow': _handle_result(cash_flow, symbol)
        }
    
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}


def get_analyst_estimates(symbol: str) -> Dict[str, Any]:
    """
    Get analyst consensus estimates
    
    Args:
        symbol: Stock ticker
    
    Returns:
        dict: Earnings estimates, revenue estimates, price targets
    
    Example:
        >>> get_analyst_estimates('AAPL')
        {'eps_estimates': [...], 'revenue_estimates': [...], 'price_target': {...}}
    
    Note:
        Requires FMP API key. Set via environment or OpenBB settings.
    """
    if not OPENBB_AVAILABLE:
        return {'error': 'OpenBB not installed', 'symbol': symbol}
    
    try:
        # Try FMP provider (requires API key)
        consensus = obb.equity.estimates.consensus(
            symbol=symbol,
            provider="fmp"
        )
        
        price_target = obb.equity.estimates.price_target(
            symbol=symbol,
            limit=50,
            provider="fmp"
        )
        
        forward_eps = obb.equity.estimates.forward_eps(
            symbol=symbol,
            provider="fmp"
        )
        
        return {
            'symbol': symbol,
            'consensus': _handle_result(consensus, symbol),
            'price_target': _handle_result(price_target, symbol),
            'forward_eps': _handle_result(forward_eps, symbol),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'note': 'Requires FMP API key. Get one at https://financialmodelingprep.com'
        }


def get_economic_calendar(
    start: Optional[str] = None,
    end: Optional[str] = None
) -> List[Dict]:
    """
    Get economic calendar events
    
    Args:
        start: Start date (YYYY-MM-DD) - defaults to today
        end: End date (YYYY-MM-DD) - defaults to 7 days from now
    
    Returns:
        list: Upcoming economic events (GDP, CPI, NFP, Fed meetings, etc.)
    
    Example:
        >>> get_economic_calendar('2024-03-01', '2024-03-31')
        [{'date': '2024-03-08', 'event': 'NFP', 'impact': 'high', ...}, ...]
    
    Note:
        Requires FMP or TradingEconomics API key.
    """
    if not OPENBB_AVAILABLE:
        return [{'error': 'OpenBB not installed'}]
    
    try:
        # Default date range if not provided
        if start is None:
            start = datetime.now().strftime('%Y-%m-%d')
        if end is None:
            end = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        result = obb.economy.calendar(
            start_date=start,
            end_date=end,
            provider="fmp"  # Requires FMP API key
        )
        
        data = _handle_result(result)
        return data if isinstance(data, list) else [data]
    
    except Exception as e:
        return [{'error': str(e), 'note': 'Requires FMP API key from https://financialmodelingprep.com'}]


def get_etf_holdings(symbol: str) -> List[Dict]:
    """
    Get ETF holdings composition
    
    Args:
        symbol: ETF ticker (e.g., 'SPY', 'QQQ')
    
    Returns:
        list: Top holdings with weights
    
    Example:
        >>> get_etf_holdings('SPY')
        [{'symbol': 'AAPL', 'name': 'Apple Inc.', 'weight': 7.2}, ...]
    
    Note:
        Requires FMP or Intrinio API key.
    """
    if not OPENBB_AVAILABLE:
        return [{'error': 'OpenBB not installed', 'symbol': symbol}]
    
    try:
        result = obb.etf.holdings(
            symbol=symbol,
            provider="fmp"  # Requires FMP API key
        )
        
        data = _handle_result(result, symbol)
        return data if isinstance(data, list) else [data]
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol, 'note': 'Requires FMP API key from https://financialmodelingprep.com'}]


def get_options_chains(symbol: str) -> Dict[str, Any]:
    """
    Get options chain data
    
    Args:
        symbol: Stock ticker
    
    Returns:
        dict: Calls and puts with strikes, expiration, greeks
    
    Example:
        >>> get_options_chains('AAPL')
        {'calls': [...], 'puts': [...], 'expirations': [...]}
    """
    if not OPENBB_AVAILABLE:
        return {'error': 'OpenBB not installed', 'symbol': symbol}
    
    try:
        result = obb.derivatives.options.chains(
            symbol=symbol,
            provider=DEFAULT_PROVIDER
        )
        
        data = _handle_result(result, symbol)
        
        # Separate calls and puts if available
        if isinstance(data, list):
            calls = [d for d in data if d.get('option_type') == 'call']
            puts = [d for d in data if d.get('option_type') == 'put']
            
            return {
                'symbol': symbol,
                'calls': calls,
                'puts': puts,
                'timestamp': datetime.now().isoformat()
            }
        
        return {'symbol': symbol, 'data': data}
    
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}


def get_insider_trading(symbol: str, limit: int = 50) -> List[Dict]:
    """
    Get insider trading transactions
    
    Args:
        symbol: Stock ticker
        limit: Max number of transactions to return
    
    Returns:
        list: Recent insider buys/sells with amounts
    
    Example:
        >>> get_insider_trading('AAPL')
        [{'date': '2024-02-15', 'insider': 'Tim Cook', 'transaction': 'sale', ...}, ...]
    """
    if not OPENBB_AVAILABLE:
        return [{'error': 'OpenBB not installed', 'symbol': symbol}]
    
    try:
        # Try FMP first (free tier available)
        result = obb.equity.ownership.insider_trading(
            symbol=symbol,
            limit=limit,
            provider="fmp"
        )
        
        data = _handle_result(result, symbol)
        return data if isinstance(data, list) else [data]
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol, 'note': 'Try provider=fmp or provider=intrinio'}]


def get_institutional_holders(symbol: str) -> List[Dict]:
    """
    Get institutional holders (13F filings)
    
    Args:
        symbol: Stock ticker
    
    Returns:
        list: Top institutional holders with positions
    
    Example:
        >>> get_institutional_holders('AAPL')
        [{'holder': 'Vanguard', 'shares': 1234567890, 'value': 123456789, ...}, ...]
    """
    if not OPENBB_AVAILABLE:
        return [{'error': 'OpenBB not installed', 'symbol': symbol}]
    
    try:
        # Try FMP first
        result = obb.equity.ownership.institutional(
            symbol=symbol,
            provider="fmp"
        )
        
        data = _handle_result(result, symbol)
        return data if isinstance(data, list) else [data]
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol, 'note': 'Try provider=fmp'}]


def get_news(symbol: str, limit: int = 20) -> List[Dict]:
    """
    Get financial news for a symbol
    
    Args:
        symbol: Stock ticker or topic
        limit: Max number of articles
    
    Returns:
        list: Recent news with title, link, date, source
    
    Example:
        >>> get_news('AAPL')
        [{'title': 'Apple...', 'url': '...', 'published': '...', 'source': '...'}, ...]
    """
    if not OPENBB_AVAILABLE:
        return [{'error': 'OpenBB not installed', 'symbol': symbol}]
    
    try:
        result = obb.news.company(
            symbol=symbol,
            limit=limit,
            provider=DEFAULT_PROVIDER
        )
        
        data = _handle_result(result, symbol)
        return data if isinstance(data, list) else [data]
    
    except Exception as e:
        return [{'error': str(e), 'symbol': symbol}]


# CLI interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python openbb_platform.py <command> [args]")
        print("\nCommands:")
        print("  quote SYMBOL                   Get real-time quote")
        print("  historical SYMBOL [start end]  Get historical prices")
        print("  financials SYMBOL [period]     Get financial statements")
        print("  estimates SYMBOL               Get analyst estimates")
        print("  calendar [start end]           Get economic calendar")
        print("  etf SYMBOL                     Get ETF holdings")
        print("  options SYMBOL                 Get options chain")
        print("  insider SYMBOL                 Get insider trading")
        print("  institutional SYMBOL           Get institutional holders")
        print("  news SYMBOL                    Get financial news")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'quote':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_stock_quote(sys.argv[2]), indent=2, default=str))
    
    elif command == 'historical':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        symbol = sys.argv[2]
        start = sys.argv[3] if len(sys.argv) > 3 else None
        end = sys.argv[4] if len(sys.argv) > 4 else None
        print(json.dumps(get_historical_prices(symbol, start, end), indent=2, default=str))
    
    elif command == 'financials':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        symbol = sys.argv[2]
        period = sys.argv[3] if len(sys.argv) > 3 else 'annual'
        print(json.dumps(get_financial_statements(symbol, period), indent=2, default=str))
    
    elif command == 'estimates':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_analyst_estimates(sys.argv[2]), indent=2, default=str))
    
    elif command == 'calendar':
        start = sys.argv[2] if len(sys.argv) > 2 else None
        end = sys.argv[3] if len(sys.argv) > 3 else None
        print(json.dumps(get_economic_calendar(start, end), indent=2, default=str))
    
    elif command == 'etf':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_etf_holdings(sys.argv[2]), indent=2, default=str))
    
    elif command == 'options':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_options_chains(sys.argv[2]), indent=2, default=str))
    
    elif command == 'insider':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_insider_trading(sys.argv[2]), indent=2, default=str))
    
    elif command == 'institutional':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_institutional_holders(sys.argv[2]), indent=2, default=str))
    
    elif command == 'news':
        if len(sys.argv) < 3:
            print("Error: Symbol required")
            sys.exit(1)
        print(json.dumps(get_news(sys.argv[2]), indent=2, default=str))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
