#!/usr/bin/env python3
"""
Alpha Vantage Global Markets API — Phase 701
Real-time and historical market data for global stocks, forex, crypto, and economic indicators.

Data includes:
- Global stock quotes (NSE/BSE India, Shanghai/Shenzhen China, NYSE, NASDAQ, etc.)
- Daily and intraday OHLCV price data
- Foreign exchange rates
- Cryptocurrency ratings and quotes
- Economic indicators (GDP, CPI, inflation, unemployment, etc.)
- Global symbol search

Usage:
  python modules/alpha_vantage_global_markets_api.py --quote AAPL
  python modules/alpha_vantage_global_markets_api.py --search Tesla
  python modules/alpha_vantage_global_markets_api.py --forex EUR USD
  python modules/alpha_vantage_global_markets_api.py --indicator GDP --json

Requires: ALPHA_VANTAGE_API_KEY environment variable
Free tier: 25 requests/day, 5 requests/minute
Data source: https://www.alphavantage.co/
"""

import requests
import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import time

class AlphaVantageAPI:
    """Alpha Vantage Global Markets API client"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage API client.
        
        Args:
            api_key: API key (defaults to ALPHA_VANTAGE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw-DataModule/1.0'
        })
        self.last_request_time = 0
        self.min_request_interval = 12  # 5 req/min = 12 sec between requests
    
    def _rate_limit(self):
        """Enforce rate limiting (5 requests per minute)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make API request with error handling.
        
        Returns dict with data or error message
        """
        if not self.api_key:
            return {
                'error': 'Missing API key',
                'message': 'Set ALPHA_VANTAGE_API_KEY environment variable',
                'retry_after': None
            }
        
        # Rate limiting
        self._rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                return {
                    'error': 'API error',
                    'message': data['Error Message'],
                    'retry_after': None
                }
            
            if 'Note' in data:
                # Rate limit hit
                return {
                    'error': 'Rate limit exceeded',
                    'message': data['Note'],
                    'retry_after': 60  # Retry after 1 minute
                }
            
            if 'Information' in data:
                return {
                    'error': 'API information',
                    'message': data['Information'],
                    'retry_after': None
                }
            
            return data
            
        except requests.RequestException as e:
            return {
                'error': 'HTTP error',
                'message': str(e),
                'retry_after': None
            }
        except json.JSONDecodeError as e:
            return {
                'error': 'JSON decode error',
                'message': str(e),
                'retry_after': None
            }
        except Exception as e:
            return {
                'error': 'Unknown error',
                'message': str(e),
                'retry_after': None
            }
    
    def get_global_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for any global ticker.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'RELIANCE.BSE', '600519.SHH')
        
        Returns:
            Dict with quote data:
            {
                'symbol': str,
                'open': float,
                'high': float,
                'low': float,
                'price': float,
                'volume': int,
                'latest_trading_day': str,
                'previous_close': float,
                'change': float,
                'change_percent': str,
                'timestamp': str
            }
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol.upper()
        }
        
        result = self._make_request(params)
        
        if 'error' in result:
            return {'error': result['error'], 'message': result['message'], 
                   'symbol': symbol, 'retry_after': result.get('retry_after')}
        
        if 'Global Quote' not in result:
            return {'error': 'Invalid response', 'message': 'No quote data found', 'symbol': symbol}
        
        quote = result['Global Quote']
        
        return {
            'symbol': quote.get('01. symbol', symbol),
            'open': self._parse_float(quote.get('02. open')),
            'high': self._parse_float(quote.get('03. high')),
            'low': self._parse_float(quote.get('04. low')),
            'price': self._parse_float(quote.get('05. price')),
            'volume': self._parse_int(quote.get('06. volume')),
            'latest_trading_day': quote.get('07. latest trading day'),
            'previous_close': self._parse_float(quote.get('08. previous close')),
            'change': self._parse_float(quote.get('09. change')),
            'change_percent': quote.get('10. change percent', '').replace('%', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_daily_prices(self, symbol: str, outputsize: str = "compact") -> Dict[str, Any]:
        """
        Get daily OHLCV price data.
        
        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)
        
        Returns:
            Dict with:
            {
                'symbol': str,
                'data': [{'date': str, 'open': float, 'high': float, 'low': float, 
                         'close': float, 'volume': int}, ...],
                'count': int,
                'timestamp': str
            }
        """
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol.upper(),
            'outputsize': outputsize
        }
        
        result = self._make_request(params)
        
        if 'error' in result:
            return {'error': result['error'], 'message': result['message'], 
                   'symbol': symbol, 'retry_after': result.get('retry_after')}
        
        if 'Time Series (Daily)' not in result:
            return {'error': 'Invalid response', 'message': 'No daily data found', 'symbol': symbol}
        
        time_series = result['Time Series (Daily)']
        
        data = []
        for date, values in sorted(time_series.items(), reverse=True):
            data.append({
                'date': date,
                'open': self._parse_float(values.get('1. open')),
                'high': self._parse_float(values.get('2. high')),
                'low': self._parse_float(values.get('3. low')),
                'close': self._parse_float(values.get('4. close')),
                'volume': self._parse_int(values.get('5. volume'))
            })
        
        return {
            'symbol': symbol.upper(),
            'data': data,
            'count': len(data),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_intraday(self, symbol: str, interval: str = "5min") -> Dict[str, Any]:
        """
        Get intraday price data.
        
        Args:
            symbol: Stock symbol
            interval: '1min', '5min', '15min', '30min', '60min'
        
        Returns:
            Dict with intraday data similar to daily prices
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol.upper(),
            'interval': interval,
            'outputsize': 'compact'  # Last 100 data points
        }
        
        result = self._make_request(params)
        
        if 'error' in result:
            return {'error': result['error'], 'message': result['message'], 
                   'symbol': symbol, 'retry_after': result.get('retry_after')}
        
        key = f'Time Series ({interval})'
        if key not in result:
            return {'error': 'Invalid response', 'message': f'No {interval} data found', 'symbol': symbol}
        
        time_series = result[key]
        
        data = []
        for timestamp, values in sorted(time_series.items(), reverse=True):
            data.append({
                'timestamp': timestamp,
                'open': self._parse_float(values.get('1. open')),
                'high': self._parse_float(values.get('2. high')),
                'low': self._parse_float(values.get('3. low')),
                'close': self._parse_float(values.get('4. close')),
                'volume': self._parse_int(values.get('5. volume'))
            })
        
        return {
            'symbol': symbol.upper(),
            'interval': interval,
            'data': data,
            'count': len(data),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_forex_rate(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Get foreign exchange rate.
        
        Args:
            from_currency: Base currency (e.g., 'USD', 'EUR')
            to_currency: Quote currency (e.g., 'JPY', 'GBP')
        
        Returns:
            Dict with:
            {
                'from': str,
                'to': str,
                'rate': float,
                'bid': float,
                'ask': float,
                'timestamp': str
            }
        """
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency.upper(),
            'to_currency': to_currency.upper()
        }
        
        result = self._make_request(params)
        
        if 'error' in result:
            return {'error': result['error'], 'message': result['message'], 
                   'retry_after': result.get('retry_after')}
        
        if 'Realtime Currency Exchange Rate' not in result:
            return {'error': 'Invalid response', 'message': 'No forex data found'}
        
        fx = result['Realtime Currency Exchange Rate']
        
        return {
            'from': fx.get('1. From_Currency Code'),
            'to': fx.get('3. To_Currency Code'),
            'rate': self._parse_float(fx.get('5. Exchange Rate')),
            'bid': self._parse_float(fx.get('8. Bid Price')),
            'ask': self._parse_float(fx.get('9. Ask Price')),
            'last_refreshed': fx.get('6. Last Refreshed'),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_crypto_rating(self, symbol: str) -> Dict[str, Any]:
        """
        Get cryptocurrency fundamental rating.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
        
        Returns:
            Dict with crypto rating data
        """
        params = {
            'function': 'CRYPTO_RATING',
            'symbol': symbol.upper()
        }
        
        result = self._make_request(params)
        
        if 'error' in result:
            return {'error': result['error'], 'message': result['message'], 
                   'symbol': symbol, 'retry_after': result.get('retry_after')}
        
        if 'Crypto Rating (FCAS)' not in result:
            return {'error': 'Invalid response', 'message': 'No crypto rating found', 'symbol': symbol}
        
        rating = result['Crypto Rating (FCAS)']
        
        return {
            'symbol': rating.get('1. symbol', symbol),
            'name': rating.get('2. name'),
            'fcas_rating': rating.get('3. fcas rating'),
            'fcas_score': self._parse_int(rating.get('4. fcas score')),
            'developer_score': self._parse_int(rating.get('5. developer score')),
            'market_maturity_score': self._parse_int(rating.get('6. market maturity score')),
            'utility_score': self._parse_int(rating.get('7. utility score')),
            'last_refreshed': rating.get('8. last refreshed'),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def search_symbols(self, keywords: str) -> List[Dict[str, Any]]:
        """
        Search for ticker symbols globally.
        
        Args:
            keywords: Search keywords (e.g., 'Tesla', 'Microsoft')
        
        Returns:
            List of matching symbols:
            [
                {
                    'symbol': str,
                    'name': str,
                    'type': str,
                    'region': str,
                    'currency': str,
                    'match_score': float
                },
                ...
            ]
        """
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        result = self._make_request(params)
        
        if 'error' in result:
            return [{'error': result['error'], 'message': result['message'], 
                    'retry_after': result.get('retry_after')}]
        
        if 'bestMatches' not in result:
            return [{'error': 'Invalid response', 'message': 'No search results found'}]
        
        matches = []
        for match in result['bestMatches']:
            matches.append({
                'symbol': match.get('1. symbol'),
                'name': match.get('2. name'),
                'type': match.get('3. type'),
                'region': match.get('4. region'),
                'market_open': match.get('5. marketOpen'),
                'market_close': match.get('6. marketClose'),
                'timezone': match.get('7. timezone'),
                'currency': match.get('8. currency'),
                'match_score': self._parse_float(match.get('9. matchScore'))
            })
        
        return matches
    
    def get_economic_indicator(self, function: str, interval: Optional[str] = None) -> Dict[str, Any]:
        """
        Get economic indicator data (GDP, CPI, inflation, unemployment, etc.)
        
        Args:
            function: Economic indicator function name
                     (e.g., 'REAL_GDP', 'CPI', 'INFLATION', 'UNEMPLOYMENT', 
                      'FEDERAL_FUNDS_RATE', 'TREASURY_YIELD')
            interval: For some indicators: 'monthly', 'quarterly', 'annual'
        
        Returns:
            Dict with:
            {
                'indicator': str,
                'data': [{'date': str, 'value': float}, ...],
                'count': int,
                'timestamp': str
            }
        """
        params = {
            'function': function.upper()
        }
        
        if interval:
            params['interval'] = interval
        
        result = self._make_request(params)
        
        if 'error' in result:
            return {'error': result['error'], 'message': result['message'], 
                   'retry_after': result.get('retry_after')}
        
        # Economic indicators have 'data' key
        if 'data' not in result:
            return {'error': 'Invalid response', 'message': 'No economic data found', 
                   'function': function}
        
        data_points = []
        for point in result['data']:
            data_points.append({
                'date': point.get('date'),
                'value': self._parse_float(point.get('value'))
            })
        
        return {
            'indicator': function,
            'name': result.get('name', function),
            'interval': result.get('interval'),
            'unit': result.get('unit'),
            'data': data_points,
            'count': len(data_points),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float from string or number"""
        if value is None or value == '':
            return None
        try:
            return float(str(value).replace(',', ''))
        except (ValueError, TypeError):
            return None
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse int from string or number"""
        if value is None or value == '':
            return None
        try:
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Alpha Vantage Global Markets API — Real-time Global Market Data'
    )
    parser.add_argument('--quote', type=str, metavar='SYMBOL',
                       help='Get real-time quote for symbol')
    parser.add_argument('--daily', type=str, metavar='SYMBOL',
                       help='Get daily prices for symbol')
    parser.add_argument('--intraday', type=str, metavar='SYMBOL',
                       help='Get intraday prices for symbol')
    parser.add_argument('--interval', type=str, default='5min',
                       choices=['1min', '5min', '15min', '30min', '60min'],
                       help='Intraday interval (default: 5min)')
    parser.add_argument('--search', type=str, metavar='KEYWORDS',
                       help='Search for symbols by keywords')
    parser.add_argument('--forex', nargs=2, metavar=('FROM', 'TO'),
                       help='Get forex rate (e.g., --forex EUR USD)')
    parser.add_argument('--crypto', type=str, metavar='SYMBOL',
                       help='Get crypto rating (e.g., BTC, ETH)')
    parser.add_argument('--indicator', type=str, metavar='FUNCTION',
                       help='Get economic indicator (e.g., REAL_GDP, CPI)')
    parser.add_argument('--json', action='store_true',
                       help='Output raw JSON')
    
    args = parser.parse_args()
    
    api = AlphaVantageAPI()
    
    # Execute requested operation
    result = None
    
    if args.quote:
        result = api.get_global_quote(args.quote)
    elif args.daily:
        result = api.get_daily_prices(args.daily)
    elif args.intraday:
        result = api.get_intraday(args.intraday, args.interval)
    elif args.search:
        result = api.search_symbols(args.search)
    elif args.forex:
        result = api.get_forex_rate(args.forex[0], args.forex[1])
    elif args.crypto:
        result = api.get_crypto_rating(args.crypto)
    elif args.indicator:
        result = api.get_economic_indicator(args.indicator)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    # Pretty print based on operation type
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        print(f"   {result.get('message', 'Unknown error')}")
        if result.get('retry_after'):
            print(f"   Retry after: {result['retry_after']} seconds")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"📊 Alpha Vantage Global Markets API")
    print(f"{'='*70}\n")
    
    if args.quote:
        print(f"💹 Quote: {result['symbol']}")
        print(f"   Price:            ${result.get('price', 0):.2f}")
        print(f"   Change:           {result.get('change', 0):+.2f} ({result.get('change_percent', '0')}%)")
        print(f"   Open:             ${result.get('open', 0):.2f}")
        print(f"   High:             ${result.get('high', 0):.2f}")
        print(f"   Low:              ${result.get('low', 0):.2f}")
        print(f"   Volume:           {result.get('volume', 0):,}")
        print(f"   Previous Close:   ${result.get('previous_close', 0):.2f}")
        print(f"   Trading Day:      {result.get('latest_trading_day', 'N/A')}")
    
    elif args.search:
        print(f"🔍 Search Results for '{args.search}':\n")
        for i, match in enumerate(result[:10], 1):
            if 'error' in match:
                continue
            print(f"{i}. {match['symbol']} — {match['name']}")
            print(f"   Type: {match['type']} | Region: {match['region']} | Currency: {match['currency']}")
            print(f"   Match Score: {match.get('match_score', 0):.4f}\n")
        print(f"\nTimestamp: {datetime.utcnow().isoformat()}")
        print()
        return
    
    elif args.forex:
        print(f"💱 Forex Rate: {result['from']}/{result['to']}")
        print(f"   Exchange Rate:    {result.get('rate', 0):.6f}")
        print(f"   Bid:              {result.get('bid', 0):.6f}")
        print(f"   Ask:              {result.get('ask', 0):.6f}")
        print(f"   Last Refreshed:   {result.get('last_refreshed', 'N/A')}")
    
    elif args.crypto:
        print(f"🪙 Crypto Rating: {result['symbol']} ({result.get('name', 'N/A')})")
        print(f"   FCAS Rating:      {result.get('fcas_rating', 'N/A')}")
        print(f"   FCAS Score:       {result.get('fcas_score', 0)}/1000")
        print(f"   Developer Score:  {result.get('developer_score', 0)}")
        print(f"   Market Maturity:  {result.get('market_maturity_score', 0)}")
        print(f"   Utility Score:    {result.get('utility_score', 0)}")
    
    elif args.daily or args.intraday:
        print(f"📈 {'Daily' if args.daily else 'Intraday'} Prices: {result['symbol']}")
        print(f"   Data Points:      {result['count']}")
        if result['data']:
            latest = result['data'][0]
            date_key = 'date' if 'date' in latest else 'timestamp'
            print(f"\n   Latest ({latest[date_key]}):")
            print(f"   Open:   ${latest.get('open', 0):.2f}")
            print(f"   High:   ${latest.get('high', 0):.2f}")
            print(f"   Low:    ${latest.get('low', 0):.2f}")
            print(f"   Close:  ${latest.get('close', 0):.2f}")
            print(f"   Volume: {latest.get('volume', 0):,}")
    
    elif args.indicator:
        print(f"📊 Economic Indicator: {result.get('name', result['indicator'])}")
        print(f"   Data Points:      {result['count']}")
        if result.get('unit'):
            print(f"   Unit:             {result['unit']}")
        if result.get('interval'):
            print(f"   Interval:         {result['interval']}")
        if result['data']:
            print(f"\n   Latest 5 readings:")
            for point in result['data'][:5]:
                print(f"   {point['date']}: {point.get('value', 'N/A')}")
    
    print(f"\nTimestamp: {result.get('timestamp', datetime.utcnow().isoformat())}")
    print()


if __name__ == '__main__':
    main()
