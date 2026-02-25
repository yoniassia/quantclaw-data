#!/usr/bin/env python3
"""
Alert DSL - Domain-specific language for complex multi-condition alert rules.

Supports conditions like:
- price > 200 AND rsi < 30 AND volume > 1M
- sma(20) crosses_above sma(50)
- change_pct(5d) > 10
- macd_signal == "bullish" OR rsi < 25

Grammar:
  expression := comparison (logical_op comparison)*
  comparison := indicator operator value
  indicator  := simple_indicator | function_indicator | cross_indicator
  operator   := > | < | >= | <= | == | !=
  logical_op := AND | OR
  value      := number [suffix]
  suffix     := M | B | K | % | d
"""

import re
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


class DSLParser:
    """Parser for alert DSL expressions."""
    
    def __init__(self):
        self.indicators = {
            'price': self._get_price,
            'volume': self._get_volume,
            'rsi': self._get_rsi,
            'macd': self._get_macd,
            'macd_signal': self._get_macd_signal,
            'sma': self._get_sma,
            'ema': self._get_ema,
            'change_pct': self._get_change_pct,
            'bb_upper': self._get_bb_upper,
            'bb_lower': self._get_bb_lower,
            'atr': self._get_atr,
            'obv': self._get_obv,
        }
        
        self.operators = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
        }
        
    def parse_value(self, value_str: str) -> float:
        """Parse value with suffix (M=million, B=billion, K=thousand, %=percent)."""
        value_str = value_str.strip()
        
        if value_str.endswith('M'):
            return float(value_str[:-1]) * 1_000_000
        elif value_str.endswith('B'):
            return float(value_str[:-1]) * 1_000_000_000
        elif value_str.endswith('K'):
            return float(value_str[:-1]) * 1_000
        elif value_str.endswith('%'):
            return float(value_str[:-1])
        else:
            return float(value_str)
    
    def parse_period(self, period_str: str) -> int:
        """Parse period string like '5d', '20d', etc."""
        if period_str.endswith('d'):
            return int(period_str[:-1])
        return int(period_str)
    
    def evaluate(self, expression: str, ticker: str, data: Optional[pd.DataFrame] = None) -> Tuple[bool, str]:
        """
        Evaluate DSL expression for given ticker.
        
        Returns:
            Tuple of (result: bool, explanation: str)
        """
        try:
            # Fetch data if not provided
            if data is None:
                data = self._fetch_data(ticker)
            
            # Handle cross operators (e.g., sma(20) crosses_above sma(50))
            if 'crosses_above' in expression or 'crosses_below' in expression:
                return self._evaluate_cross(expression, ticker, data)
            
            # Split by logical operators
            expression = expression.replace('&&', 'AND').replace('||', 'OR')
            
            if ' OR ' in expression:
                parts = expression.split(' OR ')
                results = []
                explanations = []
                for part in parts:
                    result, explanation = self._evaluate_simple(part.strip(), ticker, data)
                    results.append(result)
                    explanations.append(explanation)
                final_result = any(results)
                return final_result, f"OR condition: {' OR '.join(explanations)}"
            
            if ' AND ' in expression:
                parts = expression.split(' AND ')
                results = []
                explanations = []
                for part in parts:
                    result, explanation = self._evaluate_simple(part.strip(), ticker, data)
                    results.append(result)
                    explanations.append(explanation)
                final_result = all(results)
                return final_result, f"AND condition: {' AND '.join(explanations)}"
            
            # Simple expression
            return self._evaluate_simple(expression, ticker, data)
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _evaluate_simple(self, expression: str, ticker: str, data: pd.DataFrame) -> Tuple[bool, str]:
        """Evaluate a simple comparison expression."""
        # Parse expression: indicator operator value
        pattern = r'(\w+(?:\([^)]+\))?)\s*([><=!]+)\s*([0-9.]+[MBK%]?|"[^"]*")'
        match = re.match(pattern, expression)
        
        if not match:
            raise ValueError(f"Invalid expression: {expression}")
        
        indicator_expr, operator, value_str = match.groups()
        
        # Get indicator value
        indicator_value = self._get_indicator_value(indicator_expr, ticker, data)
        
        # Parse target value
        if value_str.startswith('"') and value_str.endswith('"'):
            target_value = value_str.strip('"')
        else:
            target_value = self.parse_value(value_str)
        
        # Apply operator
        if operator not in self.operators:
            raise ValueError(f"Unknown operator: {operator}")
        
        result = self.operators[operator](indicator_value, target_value)
        
        explanation = f"{indicator_expr}={indicator_value:.2f} {operator} {target_value}"
        return result, explanation
    
    def _evaluate_cross(self, expression: str, ticker: str, data: pd.DataFrame) -> Tuple[bool, str]:
        """Evaluate cross expressions like sma(20) crosses_above sma(50)."""
        if 'crosses_above' in expression:
            parts = expression.split('crosses_above')
            cross_type = 'above'
        else:
            parts = expression.split('crosses_below')
            cross_type = 'below'
        
        indicator1_expr = parts[0].strip()
        indicator2_expr = parts[1].strip()
        
        # Get indicator values for last 2 periods
        indicator1_current = self._get_indicator_value(indicator1_expr, ticker, data)
        indicator2_current = self._get_indicator_value(indicator2_expr, ticker, data)
        
        # Get previous values
        indicator1_prev = self._get_indicator_value(indicator1_expr, ticker, data, offset=1)
        indicator2_prev = self._get_indicator_value(indicator2_expr, ticker, data, offset=1)
        
        if cross_type == 'above':
            result = (indicator1_prev <= indicator2_prev) and (indicator1_current > indicator2_current)
        else:  # below
            result = (indicator1_prev >= indicator2_prev) and (indicator1_current < indicator2_current)
        
        explanation = (
            f"{indicator1_expr} crosses {cross_type} {indicator2_expr}: "
            f"prev({indicator1_prev:.2f} vs {indicator2_prev:.2f}), "
            f"current({indicator1_current:.2f} vs {indicator2_current:.2f})"
        )
        
        return result, explanation
    
    def _get_indicator_value(self, indicator_expr: str, ticker: str, data: pd.DataFrame, offset: int = 0) -> float:
        """Get indicator value from expression (handles functions with params)."""
        # Check if it's a function call
        func_match = re.match(r'(\w+)\(([^)]+)\)', indicator_expr)
        
        if func_match:
            func_name, params_str = func_match.groups()
            if func_name not in self.indicators:
                raise ValueError(f"Unknown indicator: {func_name}")
            
            # Parse parameters
            params = [p.strip() for p in params_str.split(',')]
            
            # Call indicator function
            return self.indicators[func_name](data, params, offset)
        else:
            # Simple indicator without parameters
            if indicator_expr not in self.indicators:
                raise ValueError(f"Unknown indicator: {indicator_expr}")
            
            return self.indicators[indicator_expr](data, [], offset)
    
    def _fetch_data(self, ticker: str, period: str = '3mo') -> pd.DataFrame:
        """Fetch historical data for ticker."""
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if data.empty:
            raise ValueError(f"No data available for {ticker}")
        
        return data
    
    # Indicator implementations
    
    def _get_price(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Get current price."""
        return float(data['Close'].iloc[-1 - offset])
    
    def _get_volume(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Get current volume."""
        return float(data['Volume'].iloc[-1 - offset])
    
    def _get_rsi(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate RSI (default period=14)."""
        period = int(params[0]) if params else 14
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1 - offset])
    
    def _get_macd(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate MACD line."""
        fast = int(params[0]) if len(params) > 0 else 12
        slow = int(params[1]) if len(params) > 1 else 26
        
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        
        return float(macd.iloc[-1 - offset])
    
    def _get_macd_signal(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> str:
        """Get MACD signal (bullish/bearish)."""
        fast = int(params[0]) if len(params) > 0 else 12
        slow = int(params[1]) if len(params) > 1 else 26
        signal = int(params[2]) if len(params) > 2 else 9
        
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        
        current_macd = float(macd.iloc[-1 - offset])
        current_signal = float(macd_signal.iloc[-1 - offset])
        
        return "bullish" if current_macd > current_signal else "bearish"
    
    def _get_sma(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate Simple Moving Average."""
        period = int(params[0]) if params else 20
        sma = data['Close'].rolling(window=period).mean()
        return float(sma.iloc[-1 - offset])
    
    def _get_ema(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate Exponential Moving Average."""
        period = int(params[0]) if params else 20
        ema = data['Close'].ewm(span=period).mean()
        return float(ema.iloc[-1 - offset])
    
    def _get_change_pct(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate percentage change over period."""
        period_str = params[0] if params else '1d'
        period = self.parse_period(period_str)
        
        current_price = data['Close'].iloc[-1 - offset]
        prev_price = data['Close'].iloc[-1 - offset - period]
        
        change_pct = ((current_price - prev_price) / prev_price) * 100
        return float(change_pct)
    
    def _get_bb_upper(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate Bollinger Band upper line."""
        period = int(params[0]) if len(params) > 0 else 20
        std_dev = int(params[1]) if len(params) > 1 else 2
        
        sma = data['Close'].rolling(window=period).mean()
        std = data['Close'].rolling(window=period).std()
        upper = sma + (std * std_dev)
        
        return float(upper.iloc[-1 - offset])
    
    def _get_bb_lower(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate Bollinger Band lower line."""
        period = int(params[0]) if len(params) > 0 else 20
        std_dev = int(params[1]) if len(params) > 1 else 2
        
        sma = data['Close'].rolling(window=period).mean()
        std = data['Close'].rolling(window=period).std()
        lower = sma - (std * std_dev)
        
        return float(lower.iloc[-1 - offset])
    
    def _get_atr(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate Average True Range."""
        period = int(params[0]) if params else 14
        
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return float(atr.iloc[-1 - offset])
    
    def _get_obv(self, data: pd.DataFrame, params: List[str], offset: int = 0) -> float:
        """Calculate On-Balance Volume."""
        obv = (np.sign(data['Close'].diff()) * data['Volume']).fillna(0).cumsum()
        return float(obv.iloc[-1 - offset])


def scan_universe(expression: str, universe: List[str]) -> List[Dict[str, Any]]:
    """
    Scan a universe of tickers against an alert expression.
    
    Args:
        expression: DSL expression to evaluate
        universe: List of ticker symbols
        
    Returns:
        List of dicts with ticker, result, and explanation
    """
    parser = DSLParser()
    results = []
    
    for ticker in universe:
        try:
            result, explanation = parser.evaluate(expression, ticker)
            results.append({
                'ticker': ticker,
                'match': result,
                'explanation': explanation,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            results.append({
                'ticker': ticker,
                'match': False,
                'explanation': f"Error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
    
    return results


def get_sp500_tickers() -> List[str]:
    """Get S&P 500 ticker list from Wikipedia."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        sp500_table = tables[0]
        tickers = sp500_table['Symbol'].tolist()
        # Clean up tickers (remove dots for BRK.B -> BRK-B format)
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception:
        # Fallback to common S&P 500 stocks
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
            'V', 'UNH', 'JNJ', 'WMT', 'JPM', 'MA', 'PG', 'XOM', 'HD', 'CVX',
            'ABBV', 'LLY', 'MRK', 'KO', 'PEP', 'COST', 'AVGO', 'TMO', 'MCD'
        ]


def help_text() -> str:
    """Return help text for the DSL."""
    return """
Alert DSL Help
==============

The Alert DSL allows you to define complex multi-condition alert rules.

Supported Indicators:
  price                  - Current stock price
  volume                 - Current trading volume
  rsi([period])          - Relative Strength Index (default: 14)
  macd([fast,slow])      - MACD line (default: 12,26)
  macd_signal([f,s,sig]) - MACD signal (bullish/bearish)
  sma(period)            - Simple Moving Average
  ema(period)            - Exponential Moving Average
  change_pct(period)     - Percentage change over period (e.g., 5d)
  bb_upper([period,std]) - Bollinger Band upper (default: 20,2)
  bb_lower([period,std]) - Bollinger Band lower (default: 20,2)
  atr([period])          - Average True Range (default: 14)
  obv()                  - On-Balance Volume

Operators:
  > < >= <= == !=        - Comparison operators

Logical Operators:
  AND                    - Both conditions must be true
  OR                     - At least one condition must be true

Cross Operators:
  crosses_above          - First indicator crosses above second
  crosses_below          - First indicator crosses below second

Value Suffixes:
  M                      - Million (e.g., 1M = 1,000,000)
  B                      - Billion
  K                      - Thousand
  %                      - Percent
  d                      - Days (for periods)

Examples:
  price > 200 AND rsi < 30
      Stock price above $200 and RSI below 30 (oversold)
  
  sma(20) crosses_above sma(50)
      Golden cross pattern
  
  volume > 10M AND change_pct(1d) > 5
      High volume with 5%+ daily gain
  
  rsi < 25 OR rsi > 75
      Oversold or overbought conditions
  
  price > bb_upper() OR price < bb_lower()
      Price breaking out of Bollinger Bands
  
  macd_signal == "bullish" AND volume > 5M
      Bullish MACD crossover with high volume

Usage:
  python cli.py dsl-eval AAPL "price > 200 AND rsi < 30"
  python cli.py dsl-scan "rsi < 25" --universe SP500
  python cli.py dsl-help
"""


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python alert_dsl.py COMMAND [ARGS...]")
        print("Commands: dsl-eval, dsl-scan, dsl-help")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'dsl-help':
        print(help_text())
        sys.exit(0)
    
    elif command == 'dsl-eval':
        if len(sys.argv) < 4:
            print("Usage: python cli.py dsl-eval SYMBOL \"EXPRESSION\"")
            print('Example: python cli.py dsl-eval AAPL "price > 200 AND rsi < 30"')
            sys.exit(1)
        
        ticker = sys.argv[2]
        expression = sys.argv[3]
        
        parser = DSLParser()
        result, explanation = parser.evaluate(expression, ticker)
        
        print(json.dumps({
            'ticker': ticker,
            'expression': expression,
            'result': result,
            'explanation': explanation,
            'timestamp': datetime.now().isoformat()
        }, indent=2))
        
        sys.exit(0 if result else 1)
    
    elif command == 'dsl-scan':
        if len(sys.argv) < 3:
            print("Usage: python cli.py dsl-scan \"EXPRESSION\" [--universe SP500] [--limit N]")
            print('Example: python cli.py dsl-scan "rsi < 25" --universe SP500 --limit 10')
            sys.exit(1)
        
        expression = sys.argv[2]
        universe_name = 'SP500'
        limit = None
        
        # Parse optional arguments
        for i in range(3, len(sys.argv)):
            if sys.argv[i] == '--universe' and i + 1 < len(sys.argv):
                universe_name = sys.argv[i + 1]
            elif sys.argv[i] == '--limit' and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
        
        # Get universe tickers
        if universe_name == 'SP500':
            tickers = get_sp500_tickers()
        else:
            # For custom universe, expect comma-separated tickers
            tickers = universe_name.split(',')
        
        # Scan universe
        results = scan_universe(expression, tickers)
        
        # Filter for matches only
        matches = [r for r in results if r['match']]
        
        # Apply limit
        if limit:
            matches = matches[:limit]
        
        print(json.dumps({
            'expression': expression,
            'universe': universe_name,
            'total_scanned': len(results),
            'matches_found': len(matches),
            'matches': matches
        }, indent=2))
        
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: dsl-eval, dsl-scan, dsl-help")
        sys.exit(1)
